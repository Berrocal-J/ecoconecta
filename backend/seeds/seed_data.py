"""
Script para insertar datos semilla en PostgreSQL.
Ejecutar después de crear las tablas con Alembic.
"""
import sys
import os
import secrets

# En Docker el seed se monta en /app/seeds, mientras que localmente vive en
# database/seeds. Detectamos ambos layouts para que el mismo script funcione
# en los dos entornos.
project_root = "/app" if os.path.isdir("/app/app") else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.usuario import Usuario, TipoGenerador
from app.models.colectivo import Colectivo, TipoColectivo
from app.models.puntuacion import PuntuacionRegla
from app.models.cuenta_acceso import CuentaAcceso, RolAcceso
from app.models.recolector import Recolector
from app.models.conversacion import Contenido
from app.core.security import hash_password


def seed_database():
    db = SessionLocal()

    try:
        # Seed idempotente: no borra solicitudes, recolecciones ni historial al reiniciar.
        # Crear usuarios de prueba (hogares y unidades productivas)
        print("Creando usuarios...")
        usuarios = [
            Usuario(
                whatsapp="573001234567",
                nombre="María González",
                tipo_generador=TipoGenerador.HOGAR,
                direccion="Calle 45 # 23-10, Villas de San Pablo",
                barrio="Villas de San Pablo",
                puntos=0
            ),
            Usuario(
                whatsapp="573007654321",
                nombre="Panadería San Pablo",
                tipo_generador=TipoGenerador.UNIDAD_PRODUCTIVA,
                direccion="Carrera 32 # 15-20, Villas de San Pablo",
                barrio="Villas de San Pablo",
                puntos=0
            ),
            Usuario(
                whatsapp="573009876543",
                nombre="Carlos Rodríguez",
                tipo_generador=TipoGenerador.HOGAR,
                direccion="Calle 50 # 30-15, Villas de San Pablo",
                barrio="Villas de San Pablo",
                puntos=0
            ),
            Usuario(
                whatsapp="573005555555",
                nombre="Restaurante El Sabor",
                tipo_generador=TipoGenerador.UNIDAD_PRODUCTIVA,
                direccion="Carrera 28 # 45-10, Villas de San Pablo",
                barrio="Villas de San Pablo",
                puntos=0
            ),
        ]
        for usuario in usuarios:
            if not db.query(Usuario).filter(Usuario.whatsapp == usuario.whatsapp).first():
                db.add(usuario)
        db.commit()
        print(f"✓ Usuarios demo disponibles: {len(usuarios)}")

        # Crear colectivos
        print("Creando colectivos...")
        colectivos = [
            Colectivo(
                nombre="Colectivo de Huerteros San Pablo",
                tipo=TipoColectivo.HUERTEROS,
                whatsapp="573002222222",
                activo=1
            ),
            Colectivo(
                nombre="Colectivo de Recicladores San Pablo",
                tipo=TipoColectivo.RECICLADORES,
                whatsapp="573003333333",
                activo=1
            ),
        ]
        for colectivo in colectivos:
            if not db.query(Colectivo).filter(Colectivo.tipo == colectivo.tipo).first():
                db.add(colectivo)
        db.commit()
        print(f"✓ Colectivos demo disponibles: {len(colectivos)}")

        # Crear reglas de puntuación
        print("Creando reglas de puntuación...")
        reglas = [
            # Reglas para orgánicos
            PuntuacionRegla(
                flujo="organico",
                material="general",
                puntos_por_kg=2.0,
                puntos_base=5,
                bono_limpio=0,
                bono_separado=2,
                bono_compactado=0,
                descripcion="Puntos base para residuos orgánicos",
                activa=1
            ),
            PuntuacionRegla(
                flujo="organico",
                material="restos_cocina",
                puntos_por_kg=3.0,
                puntos_base=5,
                bono_limpio=0,
                bono_separado=3,
                bono_compactado=0,
                descripcion="Restos de cocina y cáscaras",
                activa=1
            ),
            PuntuacionRegla(
                flujo="organico",
                material="poda",
                puntos_por_kg=1.5,
                puntos_base=5,
                bono_limpio=0,
                bono_separado=2,
                bono_compactado=0,
                descripcion="Restos de poda y jardinería",
                activa=1
            ),
            # Reglas para reciclables
            PuntuacionRegla(
                flujo="reciclable",
                material="general",
                puntos_por_kg=5.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=3,
                descripcion="Puntos base para reciclables",
                activa=1
            ),
            PuntuacionRegla(
                flujo="reciclable",
                material="plastico_pet",
                puntos_por_kg=6.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=3,
                descripcion="Botellas PET",
                activa=1
            ),
            PuntuacionRegla(
                flujo="reciclable",
                material="carton",
                puntos_por_kg=4.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=3,
                descripcion="Cajas de cartón",
                activa=1
            ),
            PuntuacionRegla(
                flujo="reciclable",
                material="vidrio",
                puntos_por_kg=7.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=0,
                descripcion="Botellas de vidrio",
                activa=1
            ),
            PuntuacionRegla(
                flujo="reciclable",
                material="metal",
                puntos_por_kg=8.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=3,
                descripcion="Chatarra y metales",
                activa=1
            ),
            PuntuacionRegla(
                flujo="reciclable",
                material="papel",
                puntos_por_kg=3.0,
                puntos_base=10,
                bono_limpio=5,
                bono_separado=5,
                bono_compactado=3,
                descripcion="Papel y cartulina",
                activa=1
            ),
        ]
        for regla in reglas:
            if not db.query(PuntuacionRegla).filter(
                PuntuacionRegla.flujo == regla.flujo,
                PuntuacionRegla.material == regla.material,
            ).first():
                db.add(regla)
        db.commit()
        print(f"✓ Reglas demo disponibles: {len(reglas)}")

        cuentas = [
            ("admin", "Administrador EcoConecta", RolAcceso.ADMIN, "DEMO_ADMIN_PASSWORD"),
            ("coord_huerteros", "Coordinador de Huerteros", RolAcceso.COORD_HUERTEROS, "DEMO_HUERTEROS_PASSWORD"),
            ("coord_recicladores", "Coordinador de Recicladores", RolAcceso.COORD_RECICLADORES, "DEMO_RECICLADORES_PASSWORD"),
        ]
        for usuario, nombre, rol, password_variable in cuentas:
            if not db.query(CuentaAcceso).filter(CuentaAcceso.usuario == usuario).first():
                password = os.getenv(password_variable) or secrets.token_urlsafe(16)
                print(f"Cuenta inicial {usuario}: password generada; configura {password_variable} para una clave estable")
                db.add(CuentaAcceso(usuario=usuario, nombre=nombre, rol=rol, password_hash=hash_password(password)))
        db.commit()
        print("✓ Cuentas de coordinacion y admin disponibles")

        print("\n✅ Datos semilla insertados exitosamente")
        print("\nResumen:")
        print(f"- Usuarios: {len(usuarios)}")
        print(f"- Colectivos: {len(colectivos)}")
        print(f"- Reglas de puntuación: {len(reglas)}")

        collective_by_type = {collective.tipo: collective for collective in db.query(Colectivo).all()}
        for name, collective_type, phone in [
            ("Huertero de turno", TipoColectivo.HUERTEROS, "573002222223"),
            ("Reciclador de turno", TipoColectivo.RECICLADORES, "573003333334"),
        ]:
            collective = collective_by_type.get(collective_type)
            if collective and not db.query(Recolector).filter(Recolector.nombre == name, Recolector.colectivo_id == collective.id).first():
                db.add(Recolector(nombre=name, colectivo_id=collective.id, telefono_whatsapp=phone, activo=True))
        db.commit()

        contents = [
            ("Separacion basica", "separacion", "general", "Organicos: cascaras, restos de cocina y poda. Reciclables: plastico, carton, vidrio, metal y papel.", 1),
            ("Entrega limpia", "buenas_practicas", "reciclable", "Entrega los reciclables secos, separados y sin restos de comida. Los valores de puntos son configurables.", 2),
            ("Huerta comunitaria", "huerta", "organico", "Los organicos separados pueden apoyar procesos comunitarios de compostaje y huerta.", 3),
            ("Horarios de referencia", "horarios", "general", "Los horarios y rutas son ejemplos de operacion y deben ser validados por la Fundacion Santo Domingo.", 4),
        ]
        for title, category, flow, body, order in contents:
            if not db.query(Contenido).filter(Contenido.titulo == title).first():
                db.add(Contenido(titulo=title, categoria=category, flujo=flow, cuerpo=body, orden=order, publicado=True))
        db.commit()

    except Exception as e:
        print(f"❌ Error insertando datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
