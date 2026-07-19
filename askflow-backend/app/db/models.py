from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024)) # S3 path or local path
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # "processing" | "ready" | "failed" - set by the upload endpoint and the
    # Arq background job (app/worker.py). Plain string + a DB CHECK constraint
    # (see migration), consistent with how LLM_PROVIDER is handled elsewhere.
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="processing")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    conversation: Mapped[Optional["Conversation"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", uselist=False
    )

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    
    # Content
    text: Mapped[str] = mapped_column(Text)
    
    # Metadata for Citation (Feature 2)
    page_number: Mapped[int] = mapped_column(Integer)
    # Bounding box as normalized (0-1) per-line rectangles: [{x0,x1,top,bottom}, ...]
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Vector Embedding (Feature 1, 4, 5)
    # 1536 dimensions for OpenAI text-embedding-3-small
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Full-text search vector, DB-generated from `text` (Hybrid Search / Phase 3)
    text_search: Mapped[Optional[str]] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True), nullable=True
    )
    
    # Relationship
    document: Mapped["Document"] = relationship(back_populates="chunks")

class Conversation(Base):
    """One continuous, auto-created conversation per document (Phase 4 Stage 3)."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    document: Mapped["Document"] = relationship(back_populates="conversation")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id"
    )

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)

    # "user" | "assistant" - DB CHECK constraint in the migration.
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)

    # Assistant rows only: the citations returned alongside this answer.
    citations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # User rows only: the search scope/mode used to answer this question.
    document_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    search_mode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
