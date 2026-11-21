from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.conversacion import Contenido
from app.models.cuenta_acceso import RolAcceso

router = APIRouter(prefix="/contenidos", tags=["contenidos"])


class ContenidoBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=160)
    categoria: str = Field(..., min_length=3, max_length=40)
    flujo: str = Field(default="general", max_length=30)
    cuerpo: str = Field(..., min_length=3)
    orden: int = 0
    publicado: bool = True


class ContenidoResponse(ContenidoBase):
    id: int

    class Config:
        from_attributes = True


@router.get("", response_model=List[ContenidoResponse])
def listar_contenidos(categoria: Optional[str] = None, flujo: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Contenido).filter(Contenido.publicado.is_(True))
    if categoria:
        query = query.filter(Contenido.categoria == categoria)
    if flujo:
        query = query.filter(Contenido.flujo.in_([flujo, "general"]))
    return query.order_by(Contenido.orden, Contenido.id).all()


@router.post("", response_model=ContenidoResponse)
def crear_contenido(data: ContenidoBase, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    item = Contenido(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{contenido_id}", response_model=ContenidoResponse)
def actualizar_contenido(contenido_id: int, data: ContenidoBase, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    item = db.query(Contenido).filter(Contenido.id == contenido_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
