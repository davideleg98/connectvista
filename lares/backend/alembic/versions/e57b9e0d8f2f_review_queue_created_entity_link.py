"""review queue created entity link

Revision ID: e57b9e0d8f2f
Revises: e2798bda4cee
Create Date: 2026-09-25 09:23:15.950001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e57b9e0d8f2f'
down_revision: Union[str, None] = 'e2798bda4cee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('review_queue_item', sa.Column('created_entity_id', sa.UUID(), nullable=True))


def downgrade() -> None:
    op.drop_column('review_queue_item', 'created_entity_id')
