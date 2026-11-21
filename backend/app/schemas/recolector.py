from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class RecolectorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    colectivo_id: int
    cuenta_id: Optional[int] = None
    telefono_whatsapp: Optional[str] = Field(default=None, max_length=20)
    activo: bool = True


class RecolectorUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    cuenta_id: Optional[int] = None
    telefono_whatsapp: Optional[str] = Field(default=None, max_length=20)
    activo: Optional[bool] = None


class RecolectorResponse(BaseModel):
    id: int
    nombre: str
    colectivo_id: int
    cuenta_id: Optional[int]
    telefono_whatsapp: Optional[str]
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True
