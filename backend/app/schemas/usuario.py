from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.usuario import TipoGenerador


class UsuarioBase(BaseModel):
    whatsapp: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    tipo_generador: TipoGenerador
    direccion: str = Field(..., max_length=255)
    barrio: str = Field(default="Villas de San Pablo", max_length=100)


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    puntos: Optional[int] = None


class UsuarioResponse(UsuarioBase):
    id: int
    puntos: int
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
