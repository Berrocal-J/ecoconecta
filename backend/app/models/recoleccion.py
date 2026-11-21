from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recoleccion(Base):
    __tablename__ = "recolecciones"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=False, unique=True)
    material_nombre = Column(String(100), nullable=False)
    peso_kg = Column(Float, nullable=False)
    cualidades = Column(String(255))  # JSON string: ["limpio", "separado", "compactado"]
    observaciones = Column(Text)
    puntos_asignados = Column(Integer, default=0)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    solicitud = relationship("Solicitud", back_populates="recoleccion")
    puntuacion_historial = relationship("PuntuacionHistorial", back_populates="recoleccion", cascade="all, delete-orphan")
