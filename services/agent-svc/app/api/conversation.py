"""Conversation-agent APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_conversation_agent
from app.conversation import ConversationAgent
from app.schemas.conversation import ConversationInterpretRequest, ConversationInterpretResponse

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/interpret", response_model=ConversationInterpretResponse)
def interpret_conversation(
    request: ConversationInterpretRequest,
    agent: Annotated[ConversationAgent, Depends(get_conversation_agent)],
) -> ConversationInterpretResponse:
    return agent.interpret(request)
