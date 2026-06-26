"""add speed subtype

Revision ID: cfc8151ea9f6
Revises: 76f55fc4d72b
Create Date: 2026-06-26 15:24:50.693306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfc8151ea9f6'
down_revision: Union[str, Sequence[str], None] = '76f55fc4d72b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the 'speed' value to trainingsubtype, for the per-week speed test
    (category Prueba / subtype Velocidad)."""
    op.execute("ALTER TYPE trainingsubtype ADD VALUE IF NOT EXISTS 'speed'")


def downgrade() -> None:
    """PostgreSQL can't drop a value from an enum type; leaving 'speed' in place is
    harmless."""
    pass
