from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TipoColectivo(enum.Enum):
    HUERTEROS = "huerteros"
    RECICLADORES = "recicladores"


class Colectivo(Base):
    __tablename__ = "colectivos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoColectivo), nullable=False)
    whatsapp = Column(String(20))
    activo = Column(Integer, default=1)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
