from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PuntuacionRegla(Base):
    __tablename__ = "puntuacion_reglas"

    id = Column(Integer, primary_key=True, index=True)
    flujo = Column(String(50), nullable=False)  # "organico" o "reciclable"
    material = Column(String(100), nullable=False)
    puntos_por_kg = Column(Float, default=0)
    puntos_base = Column(Integer, default=0)
    bono_limpio = Column(Integer, default=0)
    bono_separado = Column(Integer, default=0)
    bono_compactado = Column(Integer, default=0)
    descripcion = Column(Text)
    activa = Column(Integer, default=1)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class PuntuacionHistorial(Base):
    __tablename__ = "puntuacion_historial"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    recoleccion_id = Column(Integer, ForeignKey("recolecciones.id"), nullable=False)
    puntos = Column(Integer, nullable=False)
    regla_aplicada = Column(Text, nullable=False)  # JSON string con desglose
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")
    recoleccion = relationship("Recoleccion", back_populates="puntuacion_historial")
