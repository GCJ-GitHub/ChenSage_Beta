"""FastAPI dependencies for agent-svc APIs."""

from __future__ import annotations

from fastapi import Request

from app.conversation import ConversationAgent
from app.services.prompt_registry import PromptRegistry


def get_prompt_registry(request: Request) -> PromptRegistry:
    return request.app.state.prompt_registry


def get_conversation_agent(request: Request) -> ConversationAgent:
    return request.app.state.conversation_agent
