"""Add role-based access accounts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_access_accounts"
down_revision = "0002_public_request_privacy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DO $$ BEGIN CREATE TYPE rolacceso AS ENUM ('ADMIN', 'COORD_HUERTEROS', 'COORD_RECICLADORES'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
    rol_table = postgresql.ENUM("ADMIN", "COORD_HUERTEROS", "COORD_RECICLADORES", name="rolacceso", create_type=False)
    op.create_table(
        "cuentas_acceso",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario", sa.String(80), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", rol_table, nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cuentas_acceso_usuario", "cuentas_acceso", ["usuario"])


def downgrade() -> None:
    op.drop_index("ix_cuentas_acceso_usuario", table_name="cuentas_acceso")
    op.drop_table("cuentas_acceso")
    sa.Enum(name="rolacceso").drop(op.get_bind(), checkfirst=True)
