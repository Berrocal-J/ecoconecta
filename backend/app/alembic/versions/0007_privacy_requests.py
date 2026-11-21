"""Store citizen data deletion requests."""
from alembic import op
import sqlalchemy as sa

revision = "0007_privacy_requests"
down_revision = "0006_whatsapp_core_and_operation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "solicitudes_eliminacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telefono", sa.String(20), nullable=False),
        sa.Column("motivo", sa.Text()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resuelto_en", sa.DateTime(timezone=True)),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas_acceso.id")),
    )
    op.create_index("ix_solicitudes_eliminacion_telefono", "solicitudes_eliminacion", ["telefono"])


def downgrade() -> None:
    op.drop_index("ix_solicitudes_eliminacion_telefono", table_name="solicitudes_eliminacion")
    op.drop_table("solicitudes_eliminacion")
