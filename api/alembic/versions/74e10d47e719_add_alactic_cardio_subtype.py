"""add alactic cardio subtype

Revision ID: 74e10d47e719
Revises: 9749d67e4f42
Create Date: 2026-06-24 17:03:02.151455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74e10d47e719'
down_revision: Union[str, Sequence[str], None] = '9749d67e4f42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add 'alactic' to the cardiosubtype enum. ALTER TYPE ... ADD VALUE can't run
    inside a transaction block, so commit alembic's open transaction first."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE cardiosubtype ADD VALUE IF NOT EXISTS 'alactic'")


def downgrade() -> None:
    """Postgres can't drop a single enum value; removing 'alactic' would mean
    recreating the type. No-op (the unused value is harmless)."""
    pass
