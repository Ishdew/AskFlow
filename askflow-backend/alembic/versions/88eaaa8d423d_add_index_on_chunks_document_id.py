"""add index on chunks.document_id

Revision ID: 88eaaa8d423d
Revises: f4c2bac00540
Create Date: 2026-07-19 00:38:59.562101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88eaaa8d423d'
down_revision: Union[str, Sequence[str], None] = 'f4c2bac00540'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_chunks_document_id", table_name="chunks")
