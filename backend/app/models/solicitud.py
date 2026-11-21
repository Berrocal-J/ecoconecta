from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid


class TipoResiduo(enum.Enum):
    ORGANICO = "organico"
    RECICLABLE = "reciclable"


class EstadoSolicitud(enum.Enum):
    RECIBIDA = "recibida"
    EN_REVISION = "en_revision"
    ASIGNADA = "asignada"
    PROGRAMADA = "programada"
    RECOLECTADA = "recolectada"
    CANCELADA = "cancelada"


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo_residuo = Column(Enum(TipoResiduo), nullable=False)
    estado = Column(Enum(EstadoSolicitud), default=EstadoSolicitud.RECIBIDA, nullable=False)
    direccion = Column(String(255))
    disponibilidad_horaria = Column(String(100))
    observaciones = Column(Text)
    mensaje_original = Column(Text)  # Mensaje original de WhatsApp
    material_especifico = Column(String(100))
    consentimiento_datos = Column(Boolean, nullable=False, default=False)
    consentimiento_whatsapp = Column(Boolean, nullable=False, default=False)
    consulta_token_hash = Column(String(64), unique=True, index=True)
    codigo_unico = Column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: f"ECO-{uuid.uuid4().hex[:8].upper()}"
    )
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    usuario = relationship("Usuario", backref="solicitudes")
    asignaciones = relationship("Asignacion", back_populates="solicitud", cascade="all, delete-orphan")
    recoleccion = relationship("Recoleccion", back_populates="solicitud", uselist=False, cascade="all, delete-orphan")
