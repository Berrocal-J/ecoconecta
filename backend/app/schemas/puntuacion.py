from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PuntuacionReglaBase(BaseModel):
    flujo: str = Field(..., max_length=50)
    material: str = Field(..., max_length=100)
    puntos_por_kg: float = 0
    puntos_base: int = 0
    bono_limpio: int = 0
    bono_separado: int = 0
    bono_compactado: int = 0
    descripcion: Optional[str] = None


class PuntuacionReglaCreate(PuntuacionReglaBase):
    pass


class PuntuacionReglaUpdate(BaseModel):
    puntos_por_kg: Optional[float] = None
    puntos_base: Optional[int] = None
    bono_limpio: Optional[int] = None
    bono_separado: Optional[int] = None
    bono_compactado: Optional[int] = None
    descripcion: Optional[str] = None
    activa: Optional[int] = None


class PuntuacionReglaResponse(PuntuacionReglaBase):
    id: int
    activa: int
    creado_en: datetime

    class Config:
        from_attributes = True


class PuntuacionHistorialResponse(BaseModel):
    id: int
    usuario_id: int
    recoleccion_id: int
    puntos: int
    regla_aplicada: str
    creado_en: datetime

    class Config:
        from_attributes = True
