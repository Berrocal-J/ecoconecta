from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TipoGenerador(enum.Enum):
    HOGAR = "hogar"
    UNIDAD_PRODUCTIVA = "unidad_productiva"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    whatsapp = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    tipo_generador = Column(Enum(TipoGenerador), nullable=False)
    direccion = Column(String(255), nullable=False)
    barrio = Column(String(100), default="Villas de San Pablo")
    puntos = Column(Integer, default=0)
    consentimiento_datos = Column(Boolean, nullable=False, default=False)
    consentimiento_whatsapp = Column(Boolean, nullable=False, default=False)
    consentimiento_en = Column(DateTime(timezone=True))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
