from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.core.database import Base


class HistorialEstado(Base):
    __tablename__ = "historial_estados"
    id = Column(Integer, primary_key=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=False, index=True)
    estado_anterior = Column(String(30))
    estado_nuevo = Column(String(30), nullable=False)
    cuenta_id = Column(Integer, ForeignKey("cuentas_acceso.id"))
    observacion = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class WhatsAppEvento(Base):
    __tablename__ = "whatsapp_eventos"
    id = Column(Integer, primary_key=True)
    message_id = Column(String(180), unique=True, nullable=False, index=True)
    telefono = Column(String(20), nullable=False)
    tipo = Column(String(30), nullable=False)
    payload = Column(Text, nullable=False)
    procesado = Column(Integer, nullable=False, default=0)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class WhatsAppBorrador(Base):
    __tablename__ = "whatsapp_borradores"
    id = Column(Integer, primary_key=True)
    telefono = Column(String(20), unique=True, nullable=False, index=True)
    tipo_generador = Column(String(30), nullable=True)
    tipo_residuo = Column(String(30), nullable=True)
    direccion = Column(String(255), nullable=True)
    horario = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    ultimo_texto = Column(Text, nullable=True)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
