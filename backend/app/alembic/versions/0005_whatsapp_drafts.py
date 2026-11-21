"""Store incomplete WhatsApp conversations as drafts."""
from alembic import op
import sqlalchemy as sa

revision = "0005_whatsapp_drafts"
down_revision = "0004_operational_traceability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_borradores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telefono", sa.String(20), nullable=False, unique=True),
        sa.Column("tipo_generador", sa.String(30)),
        sa.Column("tipo_residuo", sa.String(30)),
        sa.Column("direccion", sa.String(255)),
        sa.Column("horario", sa.String(100)),
        sa.Column("observaciones", sa.Text()),
        sa.Column("ultimo_texto", sa.Text()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_whatsapp_borradores_telefono", "whatsapp_borradores", ["telefono"])


def downgrade() -> None:
    op.drop_index("ix_whatsapp_borradores_telefono", table_name="whatsapp_borradores")
    op.drop_table("whatsapp_borradores")
