from sqlalchemy.orm import Session
from app.models.puntuacion import PuntuacionRegla, PuntuacionHistorial
from app.models.recoleccion import Recoleccion
from app.models.solicitud import Solicitud
from app.models.usuario import Usuario
from typing import Dict, Any
import json


class PuntuacionService:
    def __init__(self, db: Session):
        self.db = db

    def calcular_puntos(
        self,
        flujo: str,
        material: str,
        peso_kg: float,
        cualidades: list = None
    ) -> tuple[int, Dict[str, Any]]:
        """
        Calcula puntos basados en reglas configurables.
        Retorna: (puntos_totales, desglose_regla)
        """
        if cualidades is None:
            cualidades = []

        # Buscar regla activa para el flujo y material
        regla = self.db.query(PuntuacionRegla).filter(
            PuntuacionRegla.flujo == flujo,
            PuntuacionRegla.material == material,
            PuntuacionRegla.activa == 1
        ).first()

        if not regla:
            # Regla por defecto si no existe específica
            regla = self.db.query(PuntuacionRegla).filter(
                PuntuacionRegla.flujo == flujo,
                PuntuacionRegla.material == "general",
                PuntuacionRegla.activa == 1
            ).first()

        desglose = {
            "flujo": flujo,
            "material": material,
            "peso_kg": peso_kg,
            "puntos_base": regla.puntos_base if regla else 0,
            "puntos_por_kg": (regla.puntos_por_kg * peso_kg) if regla else 0,
            "bonos": {}
        }

        puntos_totales = desglose["puntos_base"] + desglose["puntos_por_kg"]

        # Aplicar bonos por cualidades
        if regla:
            cualidades_set = set(cualidades)
            if "limpio" in cualidades_set:
                puntos_totales += regla.bono_limpio
                desglose["bonos"]["limpio"] = regla.bono_limpio
            if "separado" in cualidades_set:
                puntos_totales += regla.bono_separado
                desglose["bonos"]["separado"] = regla.bono_separado
            if "compactado" in cualidades_set:
                puntos_totales += regla.bono_compactado
                desglose["bonos"]["compactado"] = regla.bono_compactado

        desglose["puntos_totales"] = puntos_totales
        return int(puntos_totales), desglose

    def asignar_puntos(self, recoleccion_id: int) -> int:
        """
        Asigna puntos a una recolección y actualiza el usuario.
        Retorna: puntos_asignados
        """
        recoleccion = self.db.query(Recoleccion).filter(
            Recoleccion.id == recoleccion_id
        ).first()

        if not recoleccion:
            raise ValueError("Recolección no encontrada")

        historial_existente = self.db.query(PuntuacionHistorial).filter(
            PuntuacionHistorial.recoleccion_id == recoleccion_id
        ).first()
        if historial_existente:
            return historial_existente.puntos

        solicitud = self.db.query(Solicitud).filter(
            Solicitud.id == recoleccion.solicitud_id
        ).first()

        if not solicitud:
            raise ValueError("Solicitud no encontrada")

        # Parsear cualidades
        cualidades = []
        if recoleccion.cualidades:
            try:
                cualidades = json.loads(recoleccion.cualidades)
            except:
                cualidades = []

        # Calcular puntos
        puntos, desglose = self.calcular_puntos(
            flujo=solicitud.tipo_residuo.value,
            material=recoleccion.material_nombre,
            peso_kg=recoleccion.peso_kg,
            cualidades=cualidades
        )

        # Actualizar recolección
        recoleccion.puntos_asignados = puntos

        # Actualizar usuario
        usuario = self.db.query(Usuario).filter(Usuario.id == solicitud.usuario_id).first()
        if usuario:
            usuario.puntos += puntos

        # Guardar historial
        historial = PuntuacionHistorial(
            usuario_id=solicitud.usuario_id,
            recoleccion_id=recoleccion_id,
            puntos=puntos,
            regla_aplicada=json.dumps(desglose, ensure_ascii=False)
        )
        self.db.add(historial)

        self.db.commit()
        self.db.refresh(recoleccion)

        return puntos
