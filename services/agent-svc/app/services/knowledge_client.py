"""HTTP client for the knowledge-base-svc retrieval boundary."""

from __future__ import annotations

import os
from typing import Any, Literal, Protocol

import httpx

KnowledgeStatus = Literal["draft", "active", "archived", "rejected"]


class KnowledgeBaseClientProtocol(Protocol):
    def search(
        self,
        *,
        task_type: str,
        status: KnowledgeStatus | None = None,
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]: ...


class HttpKnowledgeBaseClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.getenv("KNOWLEDGE_BASE_SVC_URL", "http://127.0.0.1:8014")
        ).rstrip("/")
        self.client = httpx.Client(trust_env=False)

    def search(
        self,
        *,
        task_type: str,
        status: KnowledgeStatus | None = "active",
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        response = self.client.post(
            f"{self.base_url}/knowledge-items/search",
            json={
                "task_type": task_type,
                "status": status,
                "tags": tags or [],
                "limit": limit,
            },
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        return list(body.get("items") or [])
