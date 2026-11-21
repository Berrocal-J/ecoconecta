from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.puntuacion import PuntuacionRegla, PuntuacionHistorial
from app.schemas.puntuacion import (
    PuntuacionReglaCreate,
    PuntuacionReglaUpdate,
    PuntuacionReglaResponse,
    PuntuacionHistorialResponse
)
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso

router = APIRouter(prefix="/puntuacion", tags=["puntuacion"])


@router.post("/reglas", response_model=PuntuacionReglaResponse)
def crear_regla_puntuacion(regla: PuntuacionReglaCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    nueva_regla = PuntuacionRegla(**regla.model_dump())
    db.add(nueva_regla)
    db.commit()
    db.refresh(nueva_regla)
    return nueva_regla


@router.get("/reglas", response_model=List[PuntuacionReglaResponse])
def listar_reglas(
    flujo: str = None,
    activa: int = None,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN))
):
    query = db.query(PuntuacionRegla)

    if flujo:
        query = query.filter(PuntuacionRegla.flujo == flujo)
    if activa is not None:
        query = query.filter(PuntuacionRegla.activa == activa)

    return query.all()


@router.get("/reglas/{regla_id}", response_model=PuntuacionReglaResponse)
def obtener_regla(regla_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    regla = db.query(PuntuacionRegla).filter(PuntuacionRegla.id == regla_id).first()
    if not regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return regla


@router.put("/reglas/{regla_id}", response_model=PuntuacionReglaResponse)
def actualizar_regla(
    regla_id: int,
    regla: PuntuacionReglaUpdate,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN)),
):
    db_regla = db.query(PuntuacionRegla).filter(PuntuacionRegla.id == regla_id).first()
    if not db_regla:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    update_data = regla.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_regla, key, value)

    db.commit()
    db.refresh(db_regla)
    return db_regla


@router.get("/historial", response_model=List[PuntuacionHistorialResponse])
def listar_historial(
    usuario_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN))
):
    query = db.query(PuntuacionHistorial)

    if usuario_id:
        query = query.filter(PuntuacionHistorial.usuario_id == usuario_id)

    return query.order_by(PuntuacionHistorial.creado_en.desc()).offset(skip).limit(limit).all()


@router.get("/historial/usuario/{usuario_id}", response_model=List[PuntuacionHistorialResponse])
def obtener_historial_usuario(usuario_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    historial = db.query(PuntuacionHistorial).filter(
        PuntuacionHistorial.usuario_id == usuario_id
    ).order_by(PuntuacionHistorial.creado_en.desc()).all()
    return historial
