from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Asignacion(Base):
    __tablename__ = "asignaciones"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id"), nullable=False)
    colectivo_id = Column(Integer, ForeignKey("colectivos.id"), nullable=False)
    recolector_id = Column(Integer, ForeignKey("recolectores.id"), nullable=True)
    persona_encargada = Column(String(100), nullable=False)
    fecha_programada = Column(DateTime(timezone=True))
    confirmada_en = Column(DateTime(timezone=True))
    asignado_por_cuenta_id = Column(Integer, ForeignKey("cuentas_acceso.id"))
    estado = Column(String(30), nullable=False, default="asignada")
    observaciones = Column(String(255))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    solicitud = relationship("Solicitud", back_populates="asignaciones")
    colectivo = relationship("Colectivo")
    recolector = relationship("Recolector")
