"""FastAPI dependencies for agent-svc APIs."""

from __future__ import annotations

from fastapi import Request

from app.services.prompt_registry import PromptRegistry


def get_prompt_registry(request: Request) -> PromptRegistry:
    return request.app.state.prompt_registry
