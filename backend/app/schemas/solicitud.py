from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
from app.models.solicitud import TipoResiduo, EstadoSolicitud
from app.models.usuario import TipoGenerador


class SolicitudBase(BaseModel):
    usuario_id: int
    tipo_residuo: TipoResiduo
    direccion: Optional[str] = None
    disponibilidad_horaria: Optional[str] = None
    observaciones: Optional[str] = None
    mensaje_original: Optional[str] = None
    material_especifico: Optional[str] = Field(None, max_length=100)
    consentimiento_datos: bool = False
    consentimiento_whatsapp: bool = False


class SolicitudCreate(SolicitudBase):
    pass


class SolicitudUpdate(BaseModel):
    estado: Optional[EstadoSolicitud] = None
    disponibilidad_horaria: Optional[str] = None
    observaciones: Optional[str] = None


class SolicitudResponse(SolicitudBase):
    id: int
    estado: EstadoSolicitud
    codigo_unico: str
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


class SolicitudConUsuario(SolicitudResponse):
    usuario_nombre: str
    usuario_whatsapp: str


class SolicitudPublicCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    whatsapp: str = Field(..., min_length=7, max_length=20)
    tipo_generador: TipoGenerador
    direccion: str = Field(..., min_length=5, max_length=255)
    tipo_residuo: TipoResiduo
    material_especifico: Optional[str] = Field(None, max_length=100)
    disponibilidad_horaria: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = Field(None, max_length=1000)
    consentimiento_datos: bool
    consentimiento_whatsapp: bool = False

    @model_validator(mode="after")
    def validar_consentimiento(self):
        if not self.consentimiento_datos:
            raise ValueError("Se requiere consentimiento para tratar los datos")
        return self


class SolicitudPublicResponse(BaseModel):
    codigo_unico: str
    consulta_token: str
    estado: EstadoSolicitud
    notificacion: str


class SolicitudConsultaResponse(BaseModel):
    codigo_unico: str
    estado: EstadoSolicitud
    tipo_residuo: TipoResiduo
    material_especifico: Optional[str] = None
    disponibilidad_horaria: Optional[str] = None
    puntos: int
    creado_en: datetime


class SolicitudHistorialItem(BaseModel):
    estado_anterior: Optional[str] = None
    estado_nuevo: str
    observacion: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True
