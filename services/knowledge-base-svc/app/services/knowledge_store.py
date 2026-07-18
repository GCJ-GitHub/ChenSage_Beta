"""PostgreSQL-backed knowledge store."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import session_scope
from app.models.knowledge import KnowledgeChunkModel, KnowledgeItemModel, KnowledgeSourceModel
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
    def create_item(self, request: KnowledgeItemCreate) -> KnowledgeItemResponse:
        item_id = str(uuid4())
        with session_scope() as session:
            item = KnowledgeItemModel(
                id=item_id,
                title=request.title,
                summary=request.summary,
                task_type=request.task_type,
                source_type=request.source_type,
                status=request.status,
                quality_score=request.quality_score,
                tags=self._normalize_tags(request.tags),
                item_metadata=request.metadata,
                embedding_model=request.embedding_model,
                embedding=request.embedding,
                sources=[
                    self._build_source_model(item_id, source) for source in request.sources
                ],
                chunks=[self._build_chunk_model(item_id, chunk) for chunk in request.chunks],
            )
            session.add(item)
            session.flush()
            loaded = self._get_model(session, item_id)
            if loaded is None:
                raise KnowledgeItemNotFoundError(item_id)
            return self._to_item_response(loaded)

    def get_item(self, item_id: str) -> KnowledgeItemResponse:
        with session_scope() as session:
            item = self._get_model(session, item_id)
            if item is None:
                raise KnowledgeItemNotFoundError(item_id)
            return self._to_item_response(item)

    def add_chunk(
        self,
        item_id: str,
        request: KnowledgeChunkCreate,
    ) -> KnowledgeChunkResponse:
        with session_scope() as session:
            item = self._get_model(session, item_id)
            if item is None:
                raise KnowledgeItemNotFoundError(item_id)
            chunk = self._build_chunk_model(item_id, request)
            item.chunks.append(chunk)
            item.updated_at = datetime.now(UTC)
            session.flush()
            session.refresh(chunk)
            return self._to_chunk_response(chunk)

    def add_source(
        self,
        item_id: str,
        request: KnowledgeSourceCreate,
    ) -> KnowledgeSourceResponse:
        with session_scope() as session:
            item = self._get_model(session, item_id)
            if item is None:
                raise KnowledgeItemNotFoundError(item_id)
            source = self._build_source_model(item_id, request)
            item.sources.append(source)
            item.updated_at = datetime.now(UTC)
            session.flush()
            session.refresh(source)
            return self._to_source_response(source)

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
        normalized_tags = self._normalize_tags(tags or [])
        with session_scope() as session:
            statement = (
                select(KnowledgeItemModel)
                .options(
                    joinedload(KnowledgeItemModel.sources),
                    joinedload(KnowledgeItemModel.chunks),
                )
                .order_by(KnowledgeItemModel.updated_at.desc())
            )
            if task_type:
                statement = statement.where(KnowledgeItemModel.task_type == task_type)
            if status:
                statement = statement.where(KnowledgeItemModel.status == status)
            if source_type:
                statement = statement.where(KnowledgeItemModel.source_type == source_type)
            if normalized_tags:
                statement = statement.where(KnowledgeItemModel.tags.contains(normalized_tags))
            if min_quality_score is not None:
                statement = statement.where(
                    KnowledgeItemModel.quality_score.is_not(None),
                    KnowledgeItemModel.quality_score >= min_quality_score,
                )

            items = session.execute(statement).unique().scalars().all()
            filtered = [item for item in items if self._matches_query(item, query)]
            return [self._to_item_response(item) for item in filtered[:limit]]

    @staticmethod
    def _get_model(session: Session, item_id: str) -> KnowledgeItemModel | None:
        return (
            session.execute(
                select(KnowledgeItemModel)
                .options(
                    joinedload(KnowledgeItemModel.sources),
                    joinedload(KnowledgeItemModel.chunks),
                )
                .where(KnowledgeItemModel.id == item_id)
            )
            .unique()
            .scalar_one_or_none()
        )

    def _matches_query(self, item: KnowledgeItemModel, query: str | None) -> bool:
        if not query:
            return True
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

    def _build_chunk_model(
        self,
        item_id: str,
        request: KnowledgeChunkCreate,
    ) -> KnowledgeChunkModel:
        token_count = (
            request.token_count if request.token_count is not None else len(request.text.split())
        )
        return KnowledgeChunkModel(
            id=str(uuid4()),
            item_id=item_id,
            text=request.text,
            ordinal=request.ordinal,
            token_count=token_count,
            source_refs=request.source_refs,
            chunk_metadata=request.metadata,
            embedding=request.embedding,
        )

    @staticmethod
    def _build_source_model(
        item_id: str,
        request: KnowledgeSourceCreate,
    ) -> KnowledgeSourceModel:
        return KnowledgeSourceModel(
            id=str(uuid4()),
            item_id=item_id,
            source_type=request.source_type,
            title=request.title,
            uri=request.uri,
            summary=request.summary,
            source_metadata=request.metadata,
        )

    @staticmethod
    def _normalize_tags(tags: Sequence[str]) -> list[str]:
        normalized = [tag.strip().casefold() for tag in tags if tag.strip()]
        return list(dict.fromkeys(normalized))

    def _to_item_response(self, item: KnowledgeItemModel) -> KnowledgeItemResponse:
        return KnowledgeItemResponse(
            id=item.id,
            title=item.title,
            summary=item.summary,
            task_type=item.task_type,
            source_type=item.source_type,
            status=item.status,
            quality_score=item.quality_score,
            tags=item.tags,
            metadata=item.item_metadata,
            embedding_model=item.embedding_model,
            embedding=item.embedding,
            sources=[self._to_source_response(source) for source in item.sources],
            chunks=[self._to_chunk_response(chunk) for chunk in item.chunks],
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _to_chunk_response(chunk: KnowledgeChunkModel) -> KnowledgeChunkResponse:
        return KnowledgeChunkResponse(
            id=chunk.id,
            item_id=chunk.item_id,
            text=chunk.text,
            ordinal=chunk.ordinal,
            token_count=chunk.token_count,
            source_refs=chunk.source_refs,
            metadata=chunk.chunk_metadata,
            embedding=chunk.embedding,
            created_at=chunk.created_at,
        )

    @staticmethod
    def _to_source_response(source: KnowledgeSourceModel) -> KnowledgeSourceResponse:
        return KnowledgeSourceResponse(
            id=source.id,
            item_id=source.item_id,
            source_type=source.source_type,
            title=source.title,
            uri=source.uri,
            summary=source.summary,
            metadata=source.source_metadata,
            created_at=source.created_at,
        )
