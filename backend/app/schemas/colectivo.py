from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.colectivo import TipoColectivo


class ColectivoBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    tipo: TipoColectivo
    whatsapp: Optional[str] = Field(None, max_length=20)


class ColectivoCreate(ColectivoBase):
    pass


class ColectivoUpdate(BaseModel):
    nombre: Optional[str] = None
    whatsapp: Optional[str] = None
    activo: Optional[int] = None


class ColectivoResponse(ColectivoBase):
    id: int
    activo: int
    creado_en: datetime

    class Config:
        from_attributes = True
