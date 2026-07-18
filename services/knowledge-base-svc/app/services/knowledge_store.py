"""Process-local knowledge store used before database persistence is introduced."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.knowledge import (
    KnowledgeChunkCreate,
    KnowledgeChunkResponse,
    KnowledgeItemCreate,
    KnowledgeItemResponse,
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
    KnowledgeStatus,
    SourceType,
)


class KnowledgeItemNotFoundError(KeyError):
    """Raised when a knowledge item id is not present in the store."""


class KnowledgeStore:
    def __init__(self) -> None:
        self._items: dict[str, KnowledgeItemResponse] = {}

    def create_item(self, request: KnowledgeItemCreate) -> KnowledgeItemResponse:
        item_id = str(uuid4())
        now = self._now()
        sources = [self._build_source(item_id, source, now) for source in request.sources]
        chunks = [self._build_chunk(item_id, chunk, now) for chunk in request.chunks]
        item = KnowledgeItemResponse(
            id=item_id,
            title=request.title,
            summary=request.summary,
            task_type=request.task_type,
            source_type=request.source_type,
            status=request.status,
            quality_score=request.quality_score,
            tags=self._normalize_tags(request.tags),
            metadata=request.metadata,
            embedding_model=request.embedding_model,
            embedding=request.embedding,
            sources=sources,
            chunks=chunks,
            created_at=now,
            updated_at=now,
        )
        self._items[item_id] = item
        return item

    def get_item(self, item_id: str) -> KnowledgeItemResponse:
        try:
            return self._items[item_id]
        except KeyError as exc:
            raise KnowledgeItemNotFoundError(item_id) from exc

    def add_chunk(
        self,
        item_id: str,
        request: KnowledgeChunkCreate,
    ) -> KnowledgeChunkResponse:
        item = self.get_item(item_id)
        now = self._now()
        chunk = self._build_chunk(item_id, request, now)
        self._items[item_id] = item.model_copy(
            update={"chunks": [*item.chunks, chunk], "updated_at": now},
        )
        return chunk

    def add_source(
        self,
        item_id: str,
        request: KnowledgeSourceCreate,
    ) -> KnowledgeSourceResponse:
        item = self.get_item(item_id)
        now = self._now()
        source = self._build_source(item_id, request, now)
        self._items[item_id] = item.model_copy(
            update={"sources": [*item.sources, source], "updated_at": now},
        )
        return source

    def list_items(
        self,
        *,
        task_type: str | None = None,
        status: KnowledgeStatus | None = None,
        source_type: SourceType | None = None,
        tags: Sequence[str] | None = None,
        query: str | None = None,
        min_quality_score: float | None = None,
        limit: int = 50,
    ) -> list[KnowledgeItemResponse]:
        normalized_tags = set(self._normalize_tags(tags or []))
        items = sorted(self._items.values(), key=lambda item: item.updated_at, reverse=True)
        filtered = [
            item
            for item in items
            if self._matches_item(
                item,
                task_type=task_type,
                status=status,
                source_type=source_type,
                tags=normalized_tags,
                query=query,
                min_quality_score=min_quality_score,
            )
        ]
        return filtered[:limit]

    def _matches_item(
        self,
        item: KnowledgeItemResponse,
        *,
        task_type: str | None,
        status: KnowledgeStatus | None,
        source_type: SourceType | None,
        tags: set[str],
        query: str | None,
        min_quality_score: float | None,
    ) -> bool:
        if task_type and item.task_type != task_type:
            return False
        if status and item.status != status:
            return False
        if source_type and item.source_type != source_type:
            return False
        if tags and not tags.issubset(set(item.tags)):
            return False
        if min_quality_score is not None:
            if item.quality_score is None or item.quality_score < min_quality_score:
                return False
        if query and not self._matches_query(item, query):
            return False
        return True

    def _matches_query(self, item: KnowledgeItemResponse, query: str) -> bool:
        needle = query.casefold()
        searchable = [
            item.title,
            item.summary,
            item.task_type,
            " ".join(item.tags),
            *(chunk.text for chunk in item.chunks),
            *(source.title for source in item.sources),
            *(source.summary for source in item.sources),
            *(source.uri or "" for source in item.sources),
        ]
        return any(needle in value.casefold() for value in searchable)

    def _build_chunk(
        self,
        item_id: str,
        request: KnowledgeChunkCreate,
        created_at: datetime,
    ) -> KnowledgeChunkResponse:
        return KnowledgeChunkResponse(
            id=str(uuid4()),
            item_id=item_id,
            text=request.text,
            ordinal=request.ordinal,
            token_count=request.token_count
            if request.token_count is not None
            else len(request.text.split()),
            source_refs=request.source_refs,
            metadata=request.metadata,
            embedding=request.embedding,
            created_at=created_at,
        )

    def _build_source(
        self,
        item_id: str,
        request: KnowledgeSourceCreate,
        created_at: datetime,
    ) -> KnowledgeSourceResponse:
        return KnowledgeSourceResponse(
            id=str(uuid4()),
            item_id=item_id,
            source_type=request.source_type,
            title=request.title,
            uri=request.uri,
            summary=request.summary,
            metadata=request.metadata,
            created_at=created_at,
        )

    def _normalize_tags(self, tags: Sequence[str]) -> list[str]:
        normalized = [tag.strip().casefold() for tag in tags if tag.strip()]
        return list(dict.fromkeys(normalized))

    def _now(self) -> datetime:
        return datetime.now(tz=UTC)
