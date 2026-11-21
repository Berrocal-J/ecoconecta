"""Add authenticated collector roles."""
from alembic import op

revision = "0008_collector_roles"
down_revision = "0007_privacy_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE rolacceso ADD VALUE IF NOT EXISTS 'HUERTERO'")
    op.execute("ALTER TYPE rolacceso ADD VALUE IF NOT EXISTS 'RECICLADOR'")


def downgrade() -> None:
    # PostgreSQL no permite retirar valores de un ENUM de forma segura.
    pass
