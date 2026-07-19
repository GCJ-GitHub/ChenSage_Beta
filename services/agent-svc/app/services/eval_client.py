"""HTTP client for the eval-svc boundary."""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx

from app.schemas.execution import AgentExecutionRequest


class EvalClientProtocol(Protocol):
    def evaluate(
        self,
        *,
        request: AgentExecutionRequest,
        generated_content: str,
        context: dict[str, Any],
    ) -> dict[str, Any]: ...


class HttpEvalClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("EVAL_SVC_URL", "http://127.0.0.1:8015")).rstrip(
            "/"
        )
        self.client = httpx.Client(trust_env=False)

    def evaluate(
        self,
        *,
        request: AgentExecutionRequest,
        generated_content: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        response = self.client.post(
            f"{self.base_url}/internal/evaluate",
            json={
                "task_id": request.task_id,
                "task_type": request.task_type,
                "goal": request.goal,
                "generated_content": generated_content,
                "output_format": request.output_format or "Markdown",
                "context": context,
            },
            timeout=10,
        )
        response.raise_for_status()
        return dict(response.json())
