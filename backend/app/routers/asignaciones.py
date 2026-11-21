from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.asignacion import Asignacion
from app.models.solicitud import Solicitud, EstadoSolicitud, TipoResiduo
from app.models.colectivo import Colectivo, TipoColectivo
from app.models.usuario import Usuario
from app.models.recolector import Recolector
from app.schemas.asignacion import AsignacionCreate, AsignacionResponse, ProgramacionUpdate
from datetime import datetime, timezone
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso
from app.services.estado_service import advance
from app.services.outbound_service import send_notification_logged
from app.core.config import settings

router = APIRouter(prefix="/asignaciones", tags=["asignaciones"])

@router.post("/", response_model=AsignacionResponse)
def crear_asignacion(asignacion: AsignacionCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    # Verificar que la solicitud existe
    solicitud = db.query(Solicitud).filter(Solicitud.id == asignacion.solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    if solicitud.estado in (EstadoSolicitud.RECOLECTADA, EstadoSolicitud.CANCELADA):
        raise HTTPException(status_code=409, detail="La solicitud ya no se puede asignar")
    nueva_asignacion = Asignacion(**asignacion.model_dump(), asignado_por_cuenta_id=account.id)
    db.add(nueva_asignacion)

    # advance() valida la transición y deja registro en el historial (RN-04)
    advance(db, solicitud, EstadoSolicitud.ASIGNADA, account.id, asignacion.observaciones)

    db.commit()
    db.refresh(nueva_asignacion)
    return nueva_asignacion


@router.get("/solicitud/{solicitud_id}", response_model=List[AsignacionResponse])
def obtener_asignaciones_por_solicitud(solicitud_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    solicitud = db.query(Solicitud).filter(Solicitud.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo != TipoResiduo.ORGANICO:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo != TipoResiduo.RECICLABLE:
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    asignaciones = db.query(Asignacion).filter(
        Asignacion.solicitud_id == solicitud_id
    ).all()
    return asignaciones


@router.post("/programar")
async def programar_recoleccion(programacion: ProgramacionUpdate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    """
    Programa una recolección: asigna persona, fecha/hora y notifica al usuario.
    """
    solicitud = db.query(Solicitud).filter(Solicitud.id == programacion.solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if solicitud.estado in (EstadoSolicitud.RECOLECTADA, EstadoSolicitud.CANCELADA):
        raise HTTPException(status_code=409, detail="La solicitud ya no se puede programar")

    colectivo = db.query(Colectivo).filter(
        Colectivo.id == programacion.colectivo_id,
        Colectivo.activo == 1,
    ).first()
    if not colectivo:
        raise HTTPException(status_code=404, detail="Colectivo activo no encontrado")

    tipo_esperado = (
        TipoColectivo.HUERTEROS if solicitud.tipo_residuo == TipoResiduo.ORGANICO
        else TipoColectivo.RECICLADORES
    )
    if (account.rol == RolAcceso.COORD_HUERTEROS and tipo_esperado != TipoColectivo.HUERTEROS) or (account.rol == RolAcceso.COORD_RECICLADORES and tipo_esperado != TipoColectivo.RECICLADORES):
        raise HTTPException(status_code=403, detail="Esta cuenta no puede operar este flujo")
    if colectivo.tipo != tipo_esperado:
        raise HTTPException(status_code=400, detail="El colectivo no corresponde al flujo de residuos")

    recolector = None
    if programacion.recolector_id:
        recolector = db.query(Recolector).filter(
            Recolector.id == programacion.recolector_id,
            Recolector.activo.is_(True),
        ).first()
        if not recolector or recolector.colectivo_id != colectivo.id:
            raise HTTPException(status_code=400, detail="El recolector no pertenece al colectivo seleccionado")

    # Reutiliza la asignación abierta (si el coordinador ya asignó) para no duplicar filas
    asignacion = db.query(Asignacion).filter(
        Asignacion.solicitud_id == programacion.solicitud_id,
        Asignacion.estado != "cancelada",
    ).order_by(Asignacion.id.desc()).first()
    if asignacion is None:
        asignacion = Asignacion(solicitud_id=programacion.solicitud_id, colectivo_id=programacion.colectivo_id)
    asignacion.colectivo_id = programacion.colectivo_id
    asignacion.recolector_id = programacion.recolector_id
    asignacion.persona_encargada = programacion.persona_encargada
    asignacion.observaciones = programacion.observaciones
    asignacion.fecha_programada = programacion.fecha_programada
    asignacion.confirmada_en = datetime.now(timezone.utc)
    asignacion.asignado_por_cuenta_id = account.id
    asignacion.estado = "programada"
    db.add(asignacion)

    # La acción humana de programar deja trazabilidad de los pasos operativos.
    advance(db, solicitud, EstadoSolicitud.PROGRAMADA, account.id, programacion.observaciones)

    db.commit()

    # Notificar al usuario por WhatsApp
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    if usuario and usuario.consentimiento_whatsapp:
        mensaje = (
            f"✅ Tu solicitud {solicitud.codigo_unico} ha sido programada.\n"
            f"📅 Fecha y hora: {programacion.fecha_programada.strftime('%Y-%m-%d %H:%M')}\n"
            f"👤 Persona encargada: {programacion.persona_encargada}\n"
            f"Gracias por contribuir al cuidado del medio ambiente en Villas de San Pablo."
        )
        await send_notification_logged(db, usuario.whatsapp, mensaje, settings.WHATSAPP_TEMPLATE_PROGRAMACION, solicitud.id)

    if recolector and recolector.telefono_whatsapp:
        await send_notification_logged(
            db,
            recolector.telefono_whatsapp,
            f"Nueva asignación {solicitud.codigo_unico}: {programacion.fecha_programada.strftime('%Y-%m-%d %H:%M')}. "
            "Revisa el panel para consultar los datos necesarios y registrar la recolección."
        )

    if colectivo.whatsapp:
        await send_notification_logged(
            db,
            colectivo.whatsapp,
            f"📋 Nueva recolección programada {solicitud.codigo_unico}. "
            f"Persona encargada: {programacion.persona_encargada}. "
            f"Fecha y hora: {programacion.fecha_programada.strftime('%Y-%m-%d %H:%M')}."
        )

    return {"success": True, "mensaje": "Recolección programada y notificada"}
@router.get("/recolectores/{tipo}")
def listar_recolectores(tipo: str, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    if tipo not in {"huerteros", "recicladores"}:
        raise HTTPException(status_code=400, detail="Tipo de colectivo invalido")
    if account.rol == RolAcceso.COORD_HUERTEROS and tipo != "huerteros":
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este colectivo")
    if account.rol == RolAcceso.COORD_RECICLADORES and tipo != "recicladores":
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este colectivo")
    colectivo = db.query(Colectivo).filter(Colectivo.tipo == TipoColectivo(tipo), Colectivo.activo == 1).first()
    if not colectivo:
        return []
    return db.query(Recolector).filter(Recolector.colectivo_id == colectivo.id, Recolector.activo.is_(True)).order_by(Recolector.nombre).all()
