"""Persistent WhatsApp conversation, outbound messages and collectors."""
from alembic import op
import sqlalchemy as sa

revision = "0006_whatsapp_core_and_operation"
down_revision = "0005_whatsapp_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("consentimiento_datos", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("consentimiento_whatsapp", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("consentimiento_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("asignaciones", sa.Column("recolector_id", sa.Integer(), nullable=True))

    op.create_table(
        "whatsapp_conversaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telefono", sa.String(20), nullable=False, unique=True),
        sa.Column("estado_conversacion", sa.String(50), nullable=False, server_default="inicio"),
        sa.Column("contexto", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("ultima_interaccion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_whatsapp_conversaciones_telefono", "whatsapp_conversaciones", ["telefono"])

    op.create_table(
        "whatsapp_mensajes_salientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("destino", sa.String(20), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False, server_default="text"),
        sa.Column("contenido", sa.Text()),
        sa.Column("plantilla", sa.String(120)),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("wa_message_id", sa.String(180)),
        sa.Column("solicitud_id", sa.Integer(), sa.ForeignKey("solicitudes.id")),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("enviado_en", sa.DateTime(timezone=True)),
        sa.Column("actualizado_en", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_whatsapp_mensajes_salientes_destino", "whatsapp_mensajes_salientes", ["destino"])
    op.create_index("ix_whatsapp_mensajes_salientes_estado", "whatsapp_mensajes_salientes", ["estado"])
    op.create_index("ix_whatsapp_mensajes_salientes_solicitud_id", "whatsapp_mensajes_salientes", ["solicitud_id"])

    op.create_table(
        "recolectores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("colectivo_id", sa.Integer(), sa.ForeignKey("colectivos.id"), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas_acceso.id"), unique=True),
        sa.Column("telefono_whatsapp", sa.String(20)),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recolectores_colectivo_id", "recolectores", ["colectivo_id"])
    op.create_table(
        "contenidos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(160), nullable=False),
        sa.Column("categoria", sa.String(40), nullable=False),
        sa.Column("flujo", sa.String(30), nullable=False, server_default="general"),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("publicado", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_contenidos_categoria", "contenidos", ["categoria"])
    op.create_table(
        "usuarios_piloto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("whatsapp", sa.String(20), nullable=False, unique=True),
        sa.Column("tipo_generador", sa.String(30)),
        sa.Column("notas", sa.Text()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_usuarios_piloto_whatsapp", "usuarios_piloto", ["whatsapp"])
    op.create_table(
        "login_intentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario", sa.String(80), nullable=False),
        sa.Column("ip", sa.String(80), nullable=False),
        sa.Column("exitoso", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_login_intentos_usuario", "login_intentos", ["usuario"])
    op.create_index("ix_login_intentos_ip", "login_intentos", ["ip"])
    op.create_index("ix_login_intentos_creado_en", "login_intentos", ["creado_en"])

    op.create_foreign_key("fk_asignaciones_recolector", "asignaciones", "recolectores", ["recolector_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_asignaciones_recolector", "asignaciones", type_="foreignkey")
    op.drop_index("ix_login_intentos_creado_en", table_name="login_intentos")
    op.drop_index("ix_login_intentos_ip", table_name="login_intentos")
    op.drop_index("ix_login_intentos_usuario", table_name="login_intentos")
    op.drop_table("login_intentos")
    op.drop_index("ix_usuarios_piloto_whatsapp", table_name="usuarios_piloto")
    op.drop_table("usuarios_piloto")
    op.drop_index("ix_contenidos_categoria", table_name="contenidos")
    op.drop_table("contenidos")
    op.drop_index("ix_recolectores_colectivo_id", table_name="recolectores")
    op.drop_table("recolectores")
    op.drop_index("ix_whatsapp_mensajes_salientes_solicitud_id", table_name="whatsapp_mensajes_salientes")
    op.drop_index("ix_whatsapp_mensajes_salientes_estado", table_name="whatsapp_mensajes_salientes")
    op.drop_index("ix_whatsapp_mensajes_salientes_destino", table_name="whatsapp_mensajes_salientes")
    op.drop_table("whatsapp_mensajes_salientes")
    op.drop_index("ix_whatsapp_conversaciones_telefono", table_name="whatsapp_conversaciones")
    op.drop_table("whatsapp_conversaciones")
    op.drop_column("asignaciones", "recolector_id")
    op.drop_column("usuarios", "consentimiento_en")
    op.drop_column("usuarios", "consentimiento_whatsapp")
    op.drop_column("usuarios", "consentimiento_datos")
