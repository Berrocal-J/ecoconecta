import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class WhatsAppConversacion(Base):
    __tablename__ = "whatsapp_conversaciones"

    id = Column(Integer, primary_key=True)
    telefono = Column(String(20), unique=True, nullable=False, index=True)
    estado_conversacion = Column(String(50), nullable=False, default="inicio")
    contexto = Column(Text, nullable=False, default="{}")
    ultima_interaccion = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def get_context(self) -> dict:
        try:
            value = json.loads(self.contexto or "{}")
            return value if isinstance(value, dict) else {}
        except (TypeError, ValueError):
            return {}

    def set_context(self, value: dict) -> None:
        self.contexto = json.dumps(value, ensure_ascii=False)


class WhatsAppMensajeSaliente(Base):
    __tablename__ = "whatsapp_mensajes_salientes"

    id = Column(Integer, primary_key=True)
    destino = Column(String(20), nullable=False, index=True)
    tipo = Column(String(30), nullable=False, default="text")
    contenido = Column(Text)
    plantilla = Column(String(120))
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    intentos = Column(Integer, nullable=False, default=0)
    error = Column(Text)
    wa_message_id = Column(String(180), index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=True, index=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    enviado_en = Column(DateTime(timezone=True))
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


class UsuarioPiloto(Base):
    __tablename__ = "usuarios_piloto"

    id = Column(Integer, primary_key=True)
    whatsapp = Column(String(20), unique=True, nullable=False, index=True)
    tipo_generador = Column(String(30))
    notas = Column(Text)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Contenido(Base):
    __tablename__ = "contenidos"

    id = Column(Integer, primary_key=True)
    titulo = Column(String(160), nullable=False)
    categoria = Column(String(40), nullable=False, index=True)
    flujo = Column(String(30), nullable=False, default="general")
    cuerpo = Column(Text, nullable=False)
    orden = Column(Integer, nullable=False, default=0)
    publicado = Column(Boolean, nullable=False, default=True)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LoginIntento(Base):
    __tablename__ = "login_intentos"

    id = Column(Integer, primary_key=True)
    usuario = Column(String(80), nullable=False, index=True)
    ip = Column(String(80), nullable=False, index=True)
    exitoso = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class SolicitudEliminacion(Base):
    __tablename__ = "solicitudes_eliminacion"

    id = Column(Integer, primary_key=True)
    telefono = Column(String(20), nullable=False, index=True)
    motivo = Column(Text)
    estado = Column(String(20), nullable=False, default="pendiente")
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resuelto_en = Column(DateTime(timezone=True))
    cuenta_id = Column(Integer, ForeignKey("cuentas_acceso.id"), nullable=True)

