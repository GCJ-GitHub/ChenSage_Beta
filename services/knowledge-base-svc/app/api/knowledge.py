"""Knowledge item APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_knowledge_store
from app.schemas.knowledge import (
    KnowledgeChunkCreate,
    KnowledgeChunkResponse,
    KnowledgeItemCreate,
    KnowledgeItemResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
    KnowledgeStatus,
    SourceType,
)
from app.services.knowledge_store import KnowledgeItemNotFoundError, KnowledgeStore

router = APIRouter(prefix="/knowledge-items", tags=["knowledge-items"])


@router.get("", response_model=list[KnowledgeItemResponse])
def list_knowledge_items(
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
    task_type: Annotated[str | None, Query(max_length=80)] = None,
    status_filter: Annotated[KnowledgeStatus | None, Query(alias="status")] = None,
    source_type: SourceType | None = None,
    tag: Annotated[str | None, Query(max_length=80)] = None,
    query: Annotated[str | None, Query(max_length=500)] = None,
    min_quality_score: Annotated[float | None, Query(ge=0, le=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[KnowledgeItemResponse]:
    return store.list_items(
        task_type=task_type,
        status=status_filter,
        source_type=source_type,
        tags=[tag] if tag else None,
        query=query,
        min_quality_score=min_quality_score,
        limit=limit,
    )


@router.post("", response_model=KnowledgeItemResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_item(
    request: KnowledgeItemCreate,
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
) -> KnowledgeItemResponse:
    return store.create_item(request)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge_items(
    request: KnowledgeSearchRequest,
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
) -> KnowledgeSearchResponse:
    items = store.list_items(
        task_type=request.task_type,
        status=request.status,
        source_type=request.source_type,
        tags=request.tags,
        query=request.query,
        min_quality_score=request.min_quality_score,
        limit=request.limit,
    )
    return KnowledgeSearchResponse(total=len(items), items=items)


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
def get_knowledge_item(
    item_id: str,
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
) -> KnowledgeItemResponse:
    try:
        return store.get_item(item_id)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        ) from exc


@router.post(
    "/{item_id}/chunks",
    response_model=KnowledgeChunkResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_knowledge_chunk(
    item_id: str,
    request: KnowledgeChunkCreate,
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
) -> KnowledgeChunkResponse:
    try:
        return store.add_chunk(item_id, request)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        ) from exc


@router.post(
    "/{item_id}/sources",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_knowledge_source(
    item_id: str,
    request: KnowledgeSourceCreate,
    store: Annotated[KnowledgeStore, Depends(get_knowledge_store)],
) -> KnowledgeSourceResponse:
    try:
        return store.add_source(item_id, request)
    except KnowledgeItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge item not found",
        ) from exc
