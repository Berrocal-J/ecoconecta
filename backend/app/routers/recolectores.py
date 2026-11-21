from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.asignacion import Asignacion
from app.models.cuenta_acceso import CuentaAcceso, RolAcceso
from app.models.recolector import Recolector
from app.models.solicitud import EstadoSolicitud, Solicitud
from app.models.usuario import Usuario
from app.schemas.recolector import RecolectorCreate, RecolectorUpdate, RecolectorResponse

router = APIRouter(prefix="/recolectores", tags=["recolectores"])


@router.get("/mis-asignaciones")
def mis_asignaciones(
    db: Session = Depends(get_db),
    account=Depends(require_roles(RolAcceso.HUERTERO, RolAcceso.RECICLADOR)),
):
    recolector = db.query(Recolector).filter(Recolector.cuenta_id == account.id, Recolector.activo.is_(True)).first()
    if not recolector:
        return []
    rows = db.query(Asignacion, Solicitud, Usuario).join(
        Solicitud, Asignacion.solicitud_id == Solicitud.id
    ).join(Usuario, Solicitud.usuario_id == Usuario.id).filter(
        Asignacion.recolector_id == recolector.id,
        Solicitud.estado.notin_([EstadoSolicitud.RECOLECTADA, EstadoSolicitud.CANCELADA]),
    ).order_by(Asignacion.fecha_programada.asc().nulls_last()).all()
    return [{
        "asignacion_id": asignacion.id,
        "solicitud_id": solicitud.id,
        "codigo": solicitud.codigo_unico,
        "flujo": solicitud.tipo_residuo.value,
        "estado": solicitud.estado.value,
        "fecha_programada": asignacion.fecha_programada,
        "usuario_nombre": usuario.nombre,
        "usuario_whatsapp": usuario.whatsapp,
        "direccion": solicitud.direccion,
        "observaciones": solicitud.observaciones,
    } for asignacion, solicitud, usuario in rows]


@router.get("", response_model=list[RecolectorResponse])
def listar(db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    return db.query(Recolector).order_by(Recolector.nombre).all()


@router.post("", response_model=RecolectorResponse)
def crear(data: RecolectorCreate, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    if data.cuenta_id and not db.query(CuentaAcceso).filter(CuentaAcceso.id == data.cuenta_id, CuentaAcceso.activo.is_(True)).first():
        raise HTTPException(status_code=400, detail="La cuenta asociada no existe o está inactiva")
    item = Recolector(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{recolector_id}", response_model=RecolectorResponse)
def actualizar(recolector_id: int, data: RecolectorUpdate, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    item = db.query(Recolector).filter(Recolector.id == recolector_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Recolector no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
