from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.colectivo import Colectivo, TipoColectivo
from app.schemas.colectivo import ColectivoCreate, ColectivoUpdate, ColectivoResponse
from app.core.security import require_roles
from app.models.cuenta_acceso import RolAcceso

router = APIRouter(prefix="/colectivos", tags=["colectivos"])


@router.post("/", response_model=ColectivoResponse)
def crear_colectivo(colectivo: ColectivoCreate, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    nuevo_colectivo = Colectivo(**colectivo.model_dump())
    db.add(nuevo_colectivo)
    db.commit()
    db.refresh(nuevo_colectivo)
    return nuevo_colectivo


@router.get("/", response_model=List[ColectivoResponse])
def listar_colectivos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    colectivos = db.query(Colectivo).filter(Colectivo.activo == 1).offset(skip).limit(limit).all()
    return colectivos


@router.get("/{colectivo_id}", response_model=ColectivoResponse)
def obtener_colectivo(colectivo_id: int, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN))):
    colectivo = db.query(Colectivo).filter(Colectivo.id == colectivo_id).first()
    if not colectivo:
        raise HTTPException(status_code=404, detail="Colectivo no encontrado")
    return colectivo


@router.get("/tipo/{tipo}", response_model=List[ColectivoResponse])
def obtener_colectivos_por_tipo(tipo: str, db: Session = Depends(get_db), account = Depends(require_roles(RolAcceso.ADMIN, RolAcceso.COORD_HUERTEROS, RolAcceso.COORD_RECICLADORES))):
    try:
        tipo_enum = TipoColectivo(tipo)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Tipo de colectivo invalido") from error
    if (account.rol == RolAcceso.COORD_HUERTEROS and tipo != "huerteros") or (account.rol == RolAcceso.COORD_RECICLADORES and tipo != "recicladores"):
        raise HTTPException(status_code=403, detail="Esta cuenta no puede ver este colectivo")
    colectivos = db.query(Colectivo).filter(
        Colectivo.tipo == tipo_enum,
        Colectivo.activo == 1
    ).all()
    return colectivos


@router.put("/{colectivo_id}", response_model=ColectivoResponse)
def actualizar_colectivo(
    colectivo_id: int,
    colectivo: ColectivoUpdate,
    db: Session = Depends(get_db),
    account = Depends(require_roles(RolAcceso.ADMIN)),
):
    db_colectivo = db.query(Colectivo).filter(Colectivo.id == colectivo_id).first()
    if not db_colectivo:
        raise HTTPException(status_code=404, detail="Colectivo no encontrado")

    update_data = colectivo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_colectivo, key, value)

    db.commit()
    db.refresh(db_colectivo)
    return db_colectivo
