"""add lactic acid test warmup pointer

Revision ID: b3f9c2e1a7d4
Revises: 25c5a575dc7e
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f9c2e1a7d4'
down_revision: Union[str, Sequence[str], None] = '25c5a575dc7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('lactic_acid_test_warmup',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('training_session_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['training_session_id'], ['training_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('training_session_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('lactic_acid_test_warmup')
