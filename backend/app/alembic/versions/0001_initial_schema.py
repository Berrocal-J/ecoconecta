"""Create EcoConecta initial schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_generador = postgresql.ENUM("HOGAR", "UNIDAD_PRODUCTIVA", name="tipogenerador", create_type=False)
    tipo_residuo = postgresql.ENUM("ORGANICO", "RECICLABLE", name="tiporesiduo", create_type=False)
    estado_solicitud = postgresql.ENUM(
        "RECIBIDA", "EN_REVISION", "ASIGNADA", "PROGRAMADA", "RECOLECTADA", "CANCELADA",
        name="estadosolicitud", create_type=False,
    )
    tipo_colectivo = postgresql.ENUM("HUERTEROS", "RECICLADORES", name="tipocolectivo", create_type=False)

    # PostgreSQL no soporta CREATE TYPE IF NOT EXISTS. Estos bloques hacen la
    # migración segura si un intento anterior dejó alguno de los tipos creado.
    op.execute("""DO $$ BEGIN CREATE TYPE tipogenerador AS ENUM ('HOGAR', 'UNIDAD_PRODUCTIVA'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE tiporesiduo AS ENUM ('ORGANICO', 'RECICLABLE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE estadosolicitud AS ENUM ('RECIBIDA', 'EN_REVISION', 'ASIGNADA', 'PROGRAMADA', 'RECOLECTADA', 'CANCELADA'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")
    op.execute("""DO $$ BEGIN CREATE TYPE tipocolectivo AS ENUM ('HUERTEROS', 'RECICLADORES'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;""")

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("whatsapp", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("tipo_generador", tipo_generador, nullable=False),
        sa.Column("direccion", sa.String(255), nullable=False),
        sa.Column("barrio", sa.String(100), server_default="Villas de San Pablo"),
        sa.Column("puntos", sa.Integer(), server_default="0"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("whatsapp"),
    )
    op.create_table(
        "colectivos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("tipo", tipo_colectivo, nullable=False),
        sa.Column("whatsapp", sa.String(20)),
        sa.Column("activo", sa.Integer(), server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "solicitudes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("tipo_residuo", tipo_residuo, nullable=False),
        sa.Column("estado", estado_solicitud, nullable=False, server_default="RECIBIDA"),
        sa.Column("direccion", sa.String(255)),
        sa.Column("disponibilidad_horaria", sa.String(100)),
        sa.Column("observaciones", sa.Text()),
        sa.Column("mensaje_original", sa.Text()),
        sa.Column("codigo_unico", sa.String(20), nullable=False, unique=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "asignaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.Integer(), sa.ForeignKey("solicitudes.id"), nullable=False),
        sa.Column("colectivo_id", sa.Integer(), sa.ForeignKey("colectivos.id"), nullable=False),
        sa.Column("persona_encargada", sa.String(100), nullable=False),
        sa.Column("observaciones", sa.String(255)),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "recolecciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.Integer(), sa.ForeignKey("solicitudes.id"), nullable=False, unique=True),
        sa.Column("material_nombre", sa.String(100), nullable=False),
        sa.Column("peso_kg", sa.Float(), nullable=False),
        sa.Column("cualidades", sa.String(255)),
        sa.Column("observaciones", sa.Text()),
        sa.Column("puntos_asignados", sa.Integer(), server_default="0"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "puntuacion_reglas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("flujo", sa.String(50), nullable=False),
        sa.Column("material", sa.String(100), nullable=False),
        sa.Column("puntos_por_kg", sa.Float(), server_default="0"),
        sa.Column("puntos_base", sa.Integer(), server_default="0"),
        sa.Column("bono_limpio", sa.Integer(), server_default="0"),
        sa.Column("bono_separado", sa.Integer(), server_default="0"),
        sa.Column("bono_compactado", sa.Integer(), server_default="0"),
        sa.Column("descripcion", sa.Text()),
        sa.Column("activa", sa.Integer(), server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "puntuacion_historial",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("recoleccion_id", sa.Integer(), sa.ForeignKey("recolecciones.id"), nullable=False),
        sa.Column("puntos", sa.Integer(), nullable=False),
        sa.Column("regla_aplicada", sa.Text(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in ("puntuacion_historial", "puntuacion_reglas", "recolecciones", "asignaciones", "solicitudes", "colectivos", "usuarios"):
        op.drop_table(table)
    for enum_name in ("estadosolicitud", "tiporesiduo", "tipocolectivo", "tipogenerador"):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
