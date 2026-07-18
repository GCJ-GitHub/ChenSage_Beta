"""Schemas for knowledge-base-svc APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal[
    "generated_content",
    "url",
    "pdf",
    "json",
    "rss",
    "arxiv",
    "manual",
    "task_result",
]
KnowledgeStatus = Literal["draft", "active", "archived", "rejected"]
JsonPrimitive = str | int | float | bool | None
JsonObject = dict[str, JsonPrimitive]


class KnowledgeSourceCreate(BaseModel):
    source_type: SourceType = "manual"
    title: str = Field(min_length=1, max_length=240)
    uri: str | None = Field(default=None, max_length=1000)
    summary: str = Field(default="", max_length=4000)
    metadata: JsonObject = Field(default_factory=dict)


class KnowledgeSourceResponse(KnowledgeSourceCreate):
    id: str
    item_id: str
    created_at: datetime


class KnowledgeChunkCreate(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    ordinal: int = Field(default=0, ge=0)
    token_count: int | None = Field(default=None, ge=0)
    source_refs: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
    embedding: list[float] | None = Field(
        default=None,
        description="Reserved for pgvector-backed semantic retrieval.",
    )


class KnowledgeChunkResponse(KnowledgeChunkCreate):
    id: str
    item_id: str
    created_at: datetime


class KnowledgeItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(default="", max_length=4000)
    task_type: str = Field(min_length=1, max_length=80)
    source_type: SourceType = "manual"
    status: KnowledgeStatus = "draft"
    quality_score: float | None = Field(default=None, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
    embedding_model: str | None = Field(default=None, max_length=120)
    embedding: list[float] | None = Field(
        default=None,
        description="Reserved for pgvector-backed semantic retrieval.",
    )
    chunks: list[KnowledgeChunkCreate] = Field(default_factory=list)
    sources: list[KnowledgeSourceCreate] = Field(default_factory=list)


class KnowledgeItemResponse(BaseModel):
    id: str
    title: str
    summary: str
    task_type: str
    source_type: SourceType
    status: KnowledgeStatus
    quality_score: float | None
    tags: list[str]
    metadata: JsonObject
    embedding_model: str | None
    embedding: list[float] | None
    sources: list[KnowledgeSourceResponse]
    chunks: list[KnowledgeChunkResponse]
    created_at: datetime
    updated_at: datetime


class KnowledgeSearchRequest(BaseModel):
    task_type: str | None = Field(default=None, max_length=80)
    status: KnowledgeStatus | None = None
    source_type: SourceType | None = None
    tags: list[str] = Field(default_factory=list)
    query: str | None = Field(default=None, max_length=500)
    min_quality_score: float | None = Field(default=None, ge=0, le=1)
    limit: int = Field(default=50, ge=1, le=100)


class KnowledgeSearchResponse(BaseModel):
    total: int
    items: list[KnowledgeItemResponse]
