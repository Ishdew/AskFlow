"""add tsvector text_search column and GIN index

Revision ID: f4c2bac00540
Revises: c85d41eb4896
Create Date: 2026-07-18 22:31:00.852850

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4c2bac00540'
down_revision: Union[str, Sequence[str], None] = 'c85d41eb4896'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE chunks ADD COLUMN text_search tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', text)) STORED"
    )
    op.create_index(
        "ix_chunks_text_search", "chunks", ["text_search"], postgresql_using="gin"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_chunks_text_search", table_name="chunks")
    op.drop_column("chunks", "text_search")
