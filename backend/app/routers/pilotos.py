from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.conversacion import UsuarioPiloto
from app.models.cuenta_acceso import RolAcceso
from app.services.whatsapp_service import normalize_phone

router = APIRouter(prefix="/pilotos", tags=["pilotos"])


class PilotoRequest(BaseModel):
    whatsapp: str = Field(..., min_length=7, max_length=20)
    tipo_generador: str | None = None
    notas: str | None = None
    activo: bool = True


class PilotoResponse(PilotoRequest):
    id: int

    class Config:
        from_attributes = True


@router.get("", response_model=List[PilotoResponse])
def listar_pilotos(db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    return db.query(UsuarioPiloto).order_by(UsuarioPiloto.creado_en.desc()).all()


@router.post("", response_model=PilotoResponse)
def crear_piloto(data: PilotoRequest, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    phone = normalize_phone(data.whatsapp)
    existing = db.query(UsuarioPiloto).filter(UsuarioPiloto.whatsapp == phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="El número ya está registrado como piloto")
    item = UsuarioPiloto(whatsapp=phone, tipo_generador=data.tipo_generador, notas=data.notas, activo=data.activo)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{piloto_id}", response_model=PilotoResponse)
def actualizar_piloto(piloto_id: int, data: PilotoRequest, db: Session = Depends(get_db), account=Depends(require_roles(RolAcceso.ADMIN))):
    item = db.query(UsuarioPiloto).filter(UsuarioPiloto.id == piloto_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Piloto no encontrado")
    item.whatsapp = normalize_phone(data.whatsapp)
    item.tipo_generador = data.tipo_generador
    item.notas = data.notas
    item.activo = data.activo
    db.commit()
    db.refresh(item)
    return item
