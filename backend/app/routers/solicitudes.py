from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import hashlib
import secrets
import json
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.models.solicitud import Solicitud, EstadoSolicitud, TipoResiduo
from app.models.usuario import Usuario
from app.schemas.solicitud import (
    SolicitudCreate, SolicitudUpdate, SolicitudResponse, SolicitudConUsuario,
    SolicitudPublicCreate, SolicitudPublicResponse, SolicitudConsultaResponse,
    SolicitudHistorialItem,
)
from app.models.historial import HistorialEstado
from app.services.whatsapp_service import whatsapp_service, WhatsAppSimulator, normalize_phone
from app.core.config import settings
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso
from app.services.estado_service import advance
from app.services.outbound_service import send_notification_logged
import uuid
from pydantic import BaseModel, Field

router = APIRouter(prefix="/solicitudes", tags=["solicitudes"])


class CancelacionRequest(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=255)


def generar_codigo_unico() -> str:
    return f"ECO-{str(uuid.uuid4())[:8].upper()}"


def hash_consulta_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.post("/publica", response_model=SolicitudPublicResponse, status_code=201)
async def crear_solicitud_publica(
    solicitud: SolicitudPublicCreate,
    db: Session = Depends(get_db),
):
    """Crea una solicitud ciudadana sin exponer endpoints administrativos."""
    phone = normalize_phone(solicitud.whatsapp)
    usuario = db.query(Usuario).filter(Usuario.whatsapp == phone).first()
    if usuario:
        usuario.nombre = solicitud.nombre
        usuario.direccion = solicitud.direccion
        usuario.tipo_generador = solicitud.tipo_generador
        usuario.consentimiento_datos = True
        usuario.consentimiento_whatsapp = solicitud.consentimiento_whatsapp
        usuario.consentimiento_en = datetime.now(timezone.utc)
    else:
        usuario = Usuario(
            whatsapp=phone,
            nombre=solicitud.nombre,
            tipo_generador=solicitud.tipo_generador,
            direccion=solicitud.direccion,
            barrio="Villas de San Pablo",
            consentimiento_datos=True,
            consentimiento_whatsapp=solicitud.consentimiento_whatsapp,
            consentimiento_en=datetime.now(timezone.utc),
        )
        db.add(usuario)
        db.flush()

    consulta_token = secrets.token_urlsafe(24)
    nueva_solicitud = Solicitud(
        usuario_id=usuario.id,
        tipo_residuo=solicitud.tipo_residuo,
        direccion=solicitud.direccion,
        disponibilidad_horaria=solicitud.disponibilidad_horaria,
        observaciones=solicitud.observaciones,
        material_especifico=solicitud.material_especifico,
        consentimiento_datos=solicitud.consentimiento_datos,
        consentimiento_whatsapp=solicitud.consentimiento_whatsapp,
        consulta_token_hash=hash_consulta_token(consulta_token),
        mensaje_original="Solicitud creada desde el formulario ciudadano",
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    db.add(HistorialEstado(solicitud_id=nueva_solicitud.id, estado_nuevo=nueva_solicitud.estado.value, observacion="Solicitud creada por canal ciudadano"))
    db.commit()

    notificacion = "no solicitada: no autorizaste notificaciones por WhatsApp"
    if solicitud.consentimiento_whatsapp:
        mensaje = (
            f"Solicitud {nueva_solicitud.codigo_unico} recibida. "
            "Te avisaremos cuando el coordinador confirme la recoleccion."
        )
        if isinstance(whatsapp_service, WhatsAppSimulator):
            await whatsapp_service.enviar_mensaje_texto(phone, mensaje)
            notificacion = "simulada: WhatsApp real no esta configurado"
        elif settings.USE_EXTERNAL_SERVICES:
            await whatsapp_service.enviar_mensaje_texto(usuario.whatsapp, mensaje)
            notificacion = "enviada"
        else:
            notificacion = "pendiente: WhatsApp real no esta configurado"

    return SolicitudPublicResponse(
        codigo_unico=nueva_solicitud.codigo_unico,
        consulta_token=consulta_token,
        estado=nueva_solicitud.estado,
        notificacion=notificacion,
    )


@router.post("/", response_model=SolicitudResponse)
def crear_solicitud(solicitud: SolicitudCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nueva_solicitud = Solicitud(
        **solicitud.model_dump(),
        codigo_unico=generar_codigo_unico(),
        estado=EstadoSolicitud.RECIBIDA
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud


@router.get("/", response_model=List[SolicitudConUsuario])
def listar_solicitudes(
    skip: int = 0,
    limit: int = 100,
    estado: Optional[EstadoSolicitud] = None,
    tipo_residuo: Optional[TipoResiduo] = None,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN))
):
    query = db.query(Solicitud, Usuario).join(Usuario)

    if estado:
        query = query.filter(Solicitud.estado == estado)
    if tipo_residuo:
        query = query.filter(Solicitud.tipo_residuo == tipo_residuo)

    query = query.order_by(Solicitud.creado_en.desc()).offset(skip).limit(limit)

    resultados = []
    for solicitud, usuario in query.all():
        resultados.append(SolicitudConUsuario(
            **solicitud.__dict__,
            usuario_nombre=usuario.nombre,
            usuario_whatsapp=usuario.whatsapp
        ))
    return resultados


@router.get("/publica/consulta/{codigo}", response_model=SolicitudConsultaResponse)
def consultar_solicitud_publica(codigo: str, token: str, db: Session = Depends(get_db)):
    solicitud = db.query(Solicitud).filter(
        Solicitud.codigo_unico == codigo,
        Solicitud.consulta_token_hash == hash_consulta_token(token),
    ).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Codigo o token de consulta invalidos")

    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    return SolicitudConsultaResponse(
        codigo_unico=solicitud.codigo_unico,
        estado=solicitud.estado,
        tipo_residuo=solicitud.tipo_residuo,
        material_especifico=solicitud.material_especifico,
        disponibilidad_horaria=solicitud.disponibilidad_horaria,
        puntos=usuario.puntos if usuario else 0,
        creado_en=solicitud.creado_en,
    )


@router.get("/publica/consulta/{codigo}/historial", response_model=List[SolicitudHistorialItem])
def consultar_historial_publico(codigo: str, token: str, db: Session = Depends(get_db)):
    solicitud = db.query(Solicitud).filter(Solicitud.codigo_unico == codigo, Solicitud.consulta_token_hash == hash_consulta_token(token)).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Codigo o token de consulta invalidos")
    return db.query(HistorialEstado).filter(HistorialEstado.solicitud_id == solicitud.id).order_by(HistorialEstado.creado_en.asc()).all()


@router.get("/resumen")
def resumen_operativo(
    periodo_dias: int = 30,
    db: Session = Depends(get_db),
    account=Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES)),
):
    """Conteos operativos acotados al flujo del coordinador o globales para admin."""
    periodo_dias = max(1, min(periodo_dias, 365))
    desde = datetime.now(timezone.utc) - timedelta(days=periodo_dias)
    query = db.query(Solicitud.estado, Solicitud.tipo_residuo, func.count(Solicitud.id)).filter(Solicitud.creado_en >= desde)
    if account.rol == RolAcceso.COORD_HUERTEROS:
        query = query.filter(Solicitud.tipo_residuo == TipoResiduo.ORGANICO)
    elif account.rol == RolAcceso.COORD_RECICLADORES:
        query = query.filter(Solicitud.tipo_residuo == TipoResiduo.RECICLABLE)
    rows = query.group_by(Solicitud.estado, Solicitud.tipo_residuo).all()
    por_estado = {}
    por_flujo = {}
    total = 0
    for estado, flujo, cantidad in rows:
        por_estado[estado.value] = por_estado.get(estado.value, 0) + cantidad
        por_flujo[flujo.value] = por_flujo.get(flujo.value, 0) + cantidad
        total += cantidad
    return {"periodo_dias": periodo_dias, "total": total, "por_estado": por_estado, "por_flujo": por_flujo}


@router.get("/coordinador/{tipo_colectivo}", response_model=List[SolicitudConUsuario])
def obtener_bandeja_coordinador_prioritaria(
    tipo_colectivo: str,
    estado: Optional[EstadoSolicitud] = None,
    db: Session = Depends(get_db),
    account=Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES)),
):
    if tipo_colectivo not in {"huerteros", "recicladores"}:
        raise HTTPException(status_code=400, detail="Colectivo invalido")
    if (account.rol == RolAcceso.COORD_HUERTEROS and tipo_colectivo != "huerteros") or (account.rol == RolAcceso.COORD_RECICLADORES and tipo_colectivo != "recicladores"):
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver esta bandeja")
    tipo_residuo = TipoResiduo.ORGANICO if tipo_colectivo == "huerteros" else TipoResiduo.RECICLABLE
    query = db.query(Solicitud, Usuario).join(Usuario).filter(Solicitud.tipo_residuo == tipo_residuo)
    if estado:
        query = query.filter(Solicitud.estado == estado)
    return [SolicitudConUsuario(**solicitud.__dict__, usuario_nombre=usuario.nombre, usuario_whatsapp=usuario.whatsapp) for solicitud, usuario in query.order_by(Solicitud.creado_en.desc()).all()]


@router.get("/{solicitud_id}", response_model=SolicitudConUsuario)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    return SolicitudConUsuario(
        **solicitud.__dict__,
        usuario_nombre=usuario.nombre,
        usuario_whatsapp=usuario.whatsapp
    )


@router.get("/codigo/{codigo}", response_model=SolicitudConUsuario)
def obtener_solicitud_por_codigo(codigo: str, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    solicitud = db.query(Solicitud).filter(Solicitud.codigo_unico == codigo).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    return SolicitudConUsuario(
        **solicitud.__dict__,
        usuario_nombre=usuario.nombre,
        usuario_whatsapp=usuario.whatsapp
    )


@router.put("/{solicitud_id}", response_model=SolicitudResponse)
def actualizar_solicitud(
    solicitud_id: int,
    solicitud: SolicitudUpdate,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES)),
):
    db_solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not db_solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if account.rol == RolAcceso.COORD_HUERTEROS and db_solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and db_solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")

    update_data = solicitud.model_dump(exclude_unset=True)
    requested_state = update_data.pop("estado", None)
    if requested_state is not None:
        advance(db, db_solicitud, requested_state, account.id, update_data.get("observaciones"))
    for key, value in update_data.items():
        setattr(db_solicitud, key, value)

    db.commit()
    db.refresh(db_solicitud)
    return db_solicitud


@router.post("/{solicitud_id}/cancelar", response_model=SolicitudResponse)
async def cancelar_solicitud(
    solicitud_id: int,
    data: CancelacionRequest,
    db: Session = Depends(get_db),
    account=Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES)),
):
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    advance(db, solicitud, EstadoSolicitud.CANCELADA, account.id, data.motivo)
    solicitud.observaciones = f"Cancelada: {data.motivo}"
    db.commit()
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    if usuario and solicitud.consentimiento_whatsapp:
        await send_notification_logged(db, usuario.whatsapp, f"Tu solicitud {solicitud.codigo_unico} fue cancelada. Motivo: {data.motivo}", settings.WHATSAPP_TEMPLATE_CANCELACION, solicitud.id)
    db.refresh(solicitud)
    return solicitud


@router.get("/coordinador-legacy/{tipo_colectivo}", response_model=List[SolicitudConUsuario], include_in_schema=False)
def obtener_bandeja_coordinador(
    tipo_colectivo: str,  # "huerteros" o "recicladores"
    estado: Optional[EstadoSolicitud] = None,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))
):
    """
    Obtiene la bandeja de solicitudes para un coordinador específico.
    tipo_colectivo: "huerteros" -> residuos orgánicos, "recicladores" -> residuos reciclables
    """
    if (account.rol == RolAcceso.COORD_HUERTEROS and tipo_colectivo != "huerteros") or (account.rol == RolAcceso.COORD_RECICLADORES and tipo_colectivo != "recicladores"):
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver esta bandeja")
    tipo_residuo = TipoResiduo.ORGANICO if tipo_colectivo == "huerteros" else TipoResiduo.RECICLABLE

    query = db.query(Solicitud, Usuario).join(Usuario).filter(
        Solicitud.tipo_residuo == tipo_residuo
    )

    if estado:
        query = query.filter(Solicitud.estado == estado)

    query = query.order_by(Solicitud.creado_en.desc())

    resultados = []
    for solicitud, usuario in query.all():
        resultados.append(SolicitudConUsuario(
            **solicitud.__dict__,
            usuario_nombre=usuario.nombre,
            usuario_whatsapp=usuario.whatsapp
        ))
    return resultados
