from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
from pydantic import field_validator


class AsignacionBase(BaseModel):
    solicitud_id: int
    colectivo_id: int
    recolector_id: Optional[int] = None
    persona_encargada: str = Field(..., max_length=100)
    observaciones: Optional[str] = Field(None, max_length=255)


class AsignacionCreate(AsignacionBase):
    pass


class AsignacionResponse(AsignacionBase):
    id: int
    fecha_programada: Optional[datetime] = None
    confirmada_en: Optional[datetime] = None
    asignado_por_cuenta_id: Optional[int] = None
    estado: str
    creado_en: datetime

    class Config:
        from_attributes = True


class ProgramacionUpdate(BaseModel):
    solicitud_id: int
    colectivo_id: int
    recolector_id: Optional[int] = None
    persona_encargada: str = Field(..., min_length=2, max_length=100)
    fecha_programada: datetime
    observaciones: Optional[str] = None

    @field_validator("fecha_programada")
    @classmethod
    def fecha_requerida(cls, value: datetime) -> datetime:
        # Se guarda hora local de Colombia (UTC-5, sin horario de verano).
        # Una fecha sin zona se interpreta ya como hora de Colombia.
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone(timedelta(hours=-5))).replace(tzinfo=None)
