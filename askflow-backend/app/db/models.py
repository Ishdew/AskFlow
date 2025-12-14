from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024)) # S3 path or local path
    upload_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    chunks: Mapped[List["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    
    # Content
    text: Mapped[str] = mapped_column(Text)
    
    # Metadata for Citation (Feature 2)
    page_number: Mapped[int] = mapped_column(Integer)
    # Storing bounding box as JSON: [x1, y1, x2, y2]
    bounding_box: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) 
    
    # Vector Embedding (Feature 1, 4, 5)
    # 1536 dimensions for OpenAI text-embedding-3-small
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))
    
    # Relationship
    document: Mapped["Document"] = relationship(back_populates="chunks")
