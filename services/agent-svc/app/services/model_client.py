"""HTTP client for the model-svc internal generation boundary."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Protocol

import httpx

from app.schemas.execution import AgentExecutionRequest

if TYPE_CHECKING:
    from app.harness import AgentDefinition


class ModelClientProtocol(Protocol):
    def generate(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        prompt: str,
    ) -> dict[str, Any]: ...


class HttpModelClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("MODEL_SVC_URL", "http://127.0.0.1:8012")).rstrip(
            "/"
        )
        self.client = httpx.Client(trust_env=False)

    def generate(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        prompt: str,
    ) -> dict[str, Any]:
        response = self.client.post(
            f"{self.base_url}/internal/generate",
            json={
                "task_id": request.task_id,
                "agent": agent.name,
                "task_type": request.task_type,
                "goal": request.goal,
                "prompt": prompt,
                "output_format": request.output_format or "Markdown",
                "metadata": {"template": request.template, "input": request.input},
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
