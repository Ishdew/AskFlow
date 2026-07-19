"""add conversations and messages

Revision ID: a11334e1004a
Revises: a415c51dbcaa
Create Date: 2026-07-19 11:06:58.184335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a11334e1004a'
down_revision: Union[str, Sequence[str], None] = 'a415c51dbcaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", name="uq_conversations_document_id"),
    )
    op.create_index("ix_conversations_id", "conversations", ["id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("document_ids", sa.JSON(), nullable=True),
        sa.Column("search_mode", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_id", "messages", ["id"])
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_check_constraint("ck_messages_role_valid", "messages", "role IN ('user', 'assistant')")
    op.create_check_constraint(
        "ck_messages_search_mode_valid",
        "messages",
        "search_mode IN ('vector', 'keyword', 'hybrid') OR search_mode IS NULL",
    )

    # NOTE: autogenerate also detected 'ix_chunks_document_id' and
    # 'ix_chunks_text_search' as "removed" - this is a pre-existing drift
    # (those indexes were created via raw op.create_index() in earlier
    # migrations without a matching SQLAlchemy Index() declaration on the
    # Chunk model) unrelated to this migration, so it's deliberately omitted
    # here rather than dropping working indexes.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_messages_search_mode_valid", "messages", type_="check")
    op.drop_constraint("ck_messages_role_valid", "messages", type_="check")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_id", table_name="conversations")
    op.drop_table("conversations")
