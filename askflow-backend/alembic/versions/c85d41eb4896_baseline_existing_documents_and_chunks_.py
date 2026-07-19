"""baseline: existing documents and chunks schema

Revision ID: c85d41eb4896
Revises: 
Create Date: 2026-07-18 22:29:39.695446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c85d41eb4896'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Baseline: this dev DB's tables already match the models exactly (autogenerate
    # detected zero diff), so this revision is applied via `alembic stamp head`, not
    # `upgrade`, against it. The extension bootstrap below is only exercised by a
    # fresh install (new DB) running `alembic upgrade head` from scratch.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP EXTENSION IF EXISTS vector")
