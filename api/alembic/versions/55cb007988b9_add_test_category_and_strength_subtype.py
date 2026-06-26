"""add test category and strength subtype

Revision ID: 55cb007988b9
Revises: 6be286d81b4e
Create Date: 2026-06-26 13:45:58.855856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55cb007988b9'
down_revision: Union[str, Sequence[str], None] = '6be286d81b4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the 'test' value to trainingcategory and 'strength' to trainingsubtype,
    for the per-week strength test (category Prueba / subtype Fuerza)."""
    op.execute("ALTER TYPE trainingcategory ADD VALUE IF NOT EXISTS 'test'")
    op.execute("ALTER TYPE trainingsubtype ADD VALUE IF NOT EXISTS 'strength'")


def downgrade() -> None:
    """PostgreSQL can't drop a value from an enum type; removing 'test'/'strength'
    would require recreating both types and rewriting every column that uses them.
    They're additive and harmless, so this is a no-op."""
    pass
