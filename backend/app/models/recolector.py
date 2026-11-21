from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Recolector(Base):
    __tablename__ = "recolectores"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    colectivo_id = Column(Integer, ForeignKey("colectivos.id"), nullable=False, index=True)
    cuenta_id = Column(Integer, ForeignKey("cuentas_acceso.id"), nullable=True, unique=True)
    telefono_whatsapp = Column(String(20), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

