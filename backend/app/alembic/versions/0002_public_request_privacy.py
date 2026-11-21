"""Add citizen consent and secure consultation fields.

Revision ID: 0002_public_request_privacy
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_public_request_privacy"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("solicitudes", sa.Column("material_especifico", sa.String(100), nullable=True))
    op.add_column(
        "solicitudes",
        sa.Column("consentimiento_datos", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "solicitudes",
        sa.Column("consentimiento_whatsapp", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("solicitudes", sa.Column("consulta_token_hash", sa.String(64), nullable=True))
    op.create_index("ix_solicitudes_consulta_token_hash", "solicitudes", ["consulta_token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_solicitudes_consulta_token_hash", table_name="solicitudes")
    op.drop_column("solicitudes", "consulta_token_hash")
    op.drop_column("solicitudes", "consentimiento_whatsapp")
    op.drop_column("solicitudes", "consentimiento_datos")
    op.drop_column("solicitudes", "material_especifico")
