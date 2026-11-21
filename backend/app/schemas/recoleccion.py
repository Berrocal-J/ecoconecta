from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RecoleccionBase(BaseModel):
    solicitud_id: int
    material_nombre: str = Field(..., max_length=100)
    peso_kg: float = Field(..., gt=0)
    cualidades: Optional[str] = None  # JSON string
    observaciones: Optional[str] = None


class RecoleccionCreate(RecoleccionBase):
    pass


class RecoleccionResponse(RecoleccionBase):
    id: int
    puntos_asignados: int
    creado_en: datetime

    class Config:
        from_attributes = True


class RecoleccionConDetalles(RecoleccionResponse):
    usuario_nombre: str
    usuario_whatsapp: str
    solicitud_codigo: str
    tipo_residuo: str
