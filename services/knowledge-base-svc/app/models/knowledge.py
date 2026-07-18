"""SQLAlchemy models owned by knowledge-base-svc."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class KnowledgeItemModel(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    task_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    quality_score: Mapped[float | None] = mapped_column(Float)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    item_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    embedding_model: Mapped[str | None] = mapped_column(String(120))
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    sources: Mapped[list[KnowledgeSourceModel]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="KnowledgeSourceModel.created_at",
    )
    chunks: Mapped[list[KnowledgeChunkModel]] = relationship(
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunkModel.ordinal",
    )


class KnowledgeChunkModel(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_refs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    item: Mapped[KnowledgeItemModel] = relationship(back_populates="chunks")


class KnowledgeSourceModel(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    uri: Mapped[str | None] = mapped_column(String(1000))
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    item: Mapped[KnowledgeItemModel] = relationship(back_populates="sources")


Index("ix_knowledge_items_created_at", KnowledgeItemModel.created_at)
Index("ix_knowledge_items_updated_at", KnowledgeItemModel.updated_at)
Index("ix_knowledge_items_quality_score", KnowledgeItemModel.quality_score)
Index("ix_knowledge_items_tags", KnowledgeItemModel.tags, postgresql_using="gin")
Index("ix_knowledge_chunks_created_at", KnowledgeChunkModel.created_at)
Index("ix_knowledge_chunks_ordinal", KnowledgeChunkModel.ordinal)
Index("ix_knowledge_sources_created_at", KnowledgeSourceModel.created_at)
