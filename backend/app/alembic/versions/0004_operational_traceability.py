"""Persist confirmed scheduling, state history and WhatsApp event idempotency."""
from alembic import op
import sqlalchemy as sa

revision = "0004_operational_traceability"
down_revision = "0003_access_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("asignaciones", sa.Column("fecha_programada", sa.DateTime(timezone=True), nullable=True))
    op.add_column("asignaciones", sa.Column("confirmada_en", sa.DateTime(timezone=True), nullable=True))
    op.add_column("asignaciones", sa.Column("asignado_por_cuenta_id", sa.Integer(), sa.ForeignKey("cuentas_acceso.id"), nullable=True))
    op.add_column("asignaciones", sa.Column("estado", sa.String(30), nullable=False, server_default="asignada"))
    op.create_table(
        "historial_estados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.Integer(), sa.ForeignKey("solicitudes.id"), nullable=False),
        sa.Column("estado_anterior", sa.String(30)),
        sa.Column("estado_nuevo", sa.String(30), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas_acceso.id")),
        sa.Column("observacion", sa.Text()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_historial_estados_solicitud_id", "historial_estados", ["solicitud_id"])
    op.create_table(
        "whatsapp_eventos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("message_id", sa.String(180), nullable=False, unique=True),
        sa.Column("telefono", sa.String(20), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("procesado", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_whatsapp_eventos_message_id", "whatsapp_eventos", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_eventos_message_id", table_name="whatsapp_eventos")
    op.drop_table("whatsapp_eventos")
    op.drop_index("ix_historial_estados_solicitud_id", table_name="historial_estados")
    op.drop_table("historial_estados")
    op.drop_column("asignaciones", "estado")
    op.drop_column("asignaciones", "asignado_por_cuenta_id")
    op.drop_column("asignaciones", "confirmada_en")
    op.drop_column("asignaciones", "fecha_programada")
