"""FastAPI dependencies for knowledge-base-svc APIs."""

from __future__ import annotations

from fastapi import Request

from app.services.knowledge_store import KnowledgeStore


def get_knowledge_store(request: Request) -> KnowledgeStore:
    return request.app.state.knowledge_store
