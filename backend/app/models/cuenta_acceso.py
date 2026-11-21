from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RolAcceso(enum.Enum):
    ADMIN = "admin"
    COORD_HUERTEROS = "coord_huerteros"
    COORD_RECICLADORES = "coord_recicladores"
    HUERTERO = "huertero"
    RECICLADOR = "reciclador"


class CuentaAcceso(Base):
    __tablename__ = "cuentas_acceso"
    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(80), unique=True, nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(RolAcceso), nullable=False)
    activo = Column(Boolean, nullable=False, server_default="true")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
