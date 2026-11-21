from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.recoleccion import Recoleccion
from app.models.asignacion import Asignacion
from app.models.recolector import Recolector
from app.models.solicitud import Solicitud, EstadoSolicitud
from app.models.usuario import Usuario
from app.schemas.recoleccion import RecoleccionCreate, RecoleccionResponse, RecoleccionConDetalles
from app.services.puntuacion_service import PuntuacionService
import json
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso
from app.services.estado_service import advance
from app.services.outbound_service import send_notification_logged
from app.core.config import settings

router = APIRouter(prefix="/recolecciones", tags=["recolecciones"])

@router.post("/", response_model=RecoleccionResponse)
async def crear_recoleccion(recoleccion: RecoleccionCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    # Verificar que la solicitud existe y no tiene recolección previa
    solicitud = db.query(Solicitud).filter(Solicitud.id == recoleccion.solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    if solicitud.estado not in (EstadoSolicitud.PROGRAMADA, EstadoSolicitud.ASIGNADA):
        raise HTTPException(status_code=409, detail="La solicitud debe estar asignada o programada")

    existing = db.query(Recoleccion).filter(Recoleccion.solicitud_id == recoleccion.solicitud_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="La solicitud ya tiene una recolección registrada")

    nueva_recoleccion = Recoleccion(**recoleccion.model_dump())
    db.add(nueva_recoleccion)

    advance(db, solicitud, EstadoSolicitud.RECOLECTADA, account.id, recoleccion.observaciones)

    db.commit()
    db.refresh(nueva_recoleccion)
    puntos = PuntuacionService(db).asignar_puntos(nueva_recoleccion.id)
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    if usuario and usuario.consentimiento_whatsapp:
        await send_notification_logged(
            db,
            usuario.whatsapp,
            f"Recolección registrada para {solicitud.codigo_unico}. Material: {recoleccion.material_nombre}; peso: {recoleccion.peso_kg} kg; puntos: {puntos}.",
            settings.WHATSAPP_TEMPLATE_RECOLECCION,
            solicitud.id,
        )
    return nueva_recoleccion


@router.get("/", response_model=List[RecoleccionConDetalles])
def listar_recolecciones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    query = db.query(Recoleccion, Solicitud, Usuario).join(
        Solicitud, Recoleccion.solicitud_id == Solicitud.id
    ).join(Usuario, Solicitud.usuario_id == Usuario.id)

    query = query.order_by(Recoleccion.creado_en.desc()).offset(skip).limit(limit)

    resultados = []
    for recoleccion, solicitud, usuario in query.all():
        resultados.append(RecoleccionConDetalles(
            **recoleccion.__dict__,
            usuario_nombre=usuario.nombre,
            usuario_whatsapp=usuario.whatsapp,
            solicitud_codigo=solicitud.codigo_unico,
            tipo_residuo=solicitud.tipo_residuo.value
        ))
    return resultados


@router.get("/{recoleccion_id}", response_model=RecoleccionConDetalles)
def obtener_recoleccion(recoleccion_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    recoleccion = db.query(Recoleccion).filter(Recoleccion.id == recoleccion_id).first()
    if not recoleccion:
        raise HTTPException(status_code=404, detail="Recolección no encontrada")

    solicitud = db.query(Solicitud).filter(Solicitud.id == recoleccion.solicitud_id).first()
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()

    if account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo.value != "organico":
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")
    if account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo.value != "reciclable":
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este flujo")

    return RecoleccionConDetalles(
        **recoleccion.__dict__,
        usuario_nombre=usuario.nombre,
        usuario_whatsapp=usuario.whatsapp,
        solicitud_codigo=solicitud.codigo_unico,
        tipo_residuo=solicitud.tipo_residuo.value
    )


@router.post("/registrar-con-puntos")
async def registrar_recoleccion_con_puntos(
    recoleccion: RecoleccionCreate,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES, RolAcceso.HUERTERO, RolAcceso.RECICLADOR))
):
    """
    Registra una recolección y automáticamente calcula y asigna puntos.
    Los recolectores solo pueden cerrar solicitudes que tienen asignadas.
    """
    # Verificar solicitud
    solicitud = db.query(Solicitud).filter(Solicitud.id == recoleccion.solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if (account.rol == RolAcceso.COORD_HUERTEROS and solicitud.tipo_residuo.value != "organico") or (account.rol == RolAcceso.COORD_RECICLADORES and solicitud.tipo_residuo.value != "reciclable"):
        raise HTTPException(status_code=403, detail="Esta cuenta no puede cerrar este flujo")

    if account.rol in (RolAcceso.HUERTERO, RolAcceso.RECICLADOR):
        propia = db.query(Asignacion).join(Recolector, Asignacion.recolector_id == Recolector.id).filter(
            Asignacion.solicitud_id == solicitud.id,
            Recolector.cuenta_id == account.id,
            Recolector.activo.is_(True),
        ).first()
        if not propia:
            raise HTTPException(status_code=403, detail="Esta solicitud no está asignada a tu cuenta")

    if solicitud.estado not in (EstadoSolicitud.PROGRAMADA, EstadoSolicitud.ASIGNADA):
        raise HTTPException(status_code=409, detail="La solicitud debe estar asignada o programada")

    # Verificar que no existe recolección previa
    existing = db.query(Recoleccion).filter(Recoleccion.solicitud_id == recoleccion.solicitud_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="La solicitud ya tiene una recolección registrada")

    # Crear recolección
    nueva_recoleccion = Recoleccion(**recoleccion.model_dump())
    db.add(nueva_recoleccion)

    # Actualizar estado e historial en la misma transaccion
    advance(db, solicitud, EstadoSolicitud.RECOLECTADA, account.id, recoleccion.observaciones)

    db.commit()
    db.refresh(nueva_recoleccion)

    # Calcular y asignar puntos
    puntuacion_service = PuntuacionService(db)
    puntos = puntuacion_service.asignar_puntos(nueva_recoleccion.id)

    # Notificar al usuario
    usuario = db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
    if usuario and usuario.consentimiento_whatsapp:
        # Parsear cualidades para mensaje
        cualidades = []
        if recoleccion.cualidades:
            try:
                cualidades = json.loads(recoleccion.cualidades)
            except (ValueError, TypeError):
                pass

        cualidades_texto = ", ".join(cualidades) if cualidades else "N/A"

        mensaje = (
            f"🎉 ¡Recolección registrada!\n"
            f"📦 Material: {recoleccion.material_nombre}\n"
            f"⚖️ Peso: {recoleccion.peso_kg} kg\n"
            f"✨ Cualidades: {cualidades_texto}\n"
            f"🏆 Puntos ganados: {puntos}\n"
            f"💰 Total puntos: {usuario.puntos}\n"
            f"¡Gracias por tu aporte a Villas de San Pablo!"
        )
        await send_notification_logged(db, usuario.whatsapp, mensaje, settings.WHATSAPP_TEMPLATE_RECOLECCION, solicitud.id)

    return {
        "success": True,
        "recoleccion_id": nueva_recoleccion.id,
        "puntos_asignados": puntos,
        "mensaje": "Recolección registrada y puntos asignados"
    }
