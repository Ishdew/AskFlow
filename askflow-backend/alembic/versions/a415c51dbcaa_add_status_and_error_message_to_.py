"""add status and error_message to documents

Revision ID: a415c51dbcaa
Revises: 88eaaa8d423d
Create Date: 2026-07-19 01:53:42.038343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a415c51dbcaa'
down_revision: Union[str, Sequence[str], None] = '88eaaa8d423d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default='ready' backfills the existing (already fully processed
    # via the old synchronous upload path) rows correctly - Postgres applies
    # a non-volatile default to existing rows as part of ADD COLUMN, no
    # separate UPDATE needed.
    op.add_column(
        "documents",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ready"),
    )
    op.add_column(
        "documents",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "ck_documents_status_valid",
        "documents",
        "status IN ('processing', 'ready', 'failed')",
    )
    # Change the column's default for *future* inserts to "processing" - rows
    # backfilled above by the DEFAULT 'ready' above are untouched; SET
    # DEFAULT only affects rows inserted after this point.
    op.alter_column("documents", "status", server_default="processing")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_documents_status_valid", "documents", type_="check")
    op.drop_column("documents", "error_message")
    op.drop_column("documents", "status")
