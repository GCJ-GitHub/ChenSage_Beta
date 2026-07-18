"""Schemas for conversation-agent task interpretation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=5000)


class ConversationInterpretRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    history: list[ConversationMessage] = Field(default_factory=list)
    output_format: str = Field(default="Markdown", max_length=80)


class ConversationTemplateChoice(BaseModel):
    id: str
    name: str
    version: str


class ConversationTaskDraft(BaseModel):
    task_type: str
    goal: str
    template: str
    output_format: str
    input: dict[str, Any] = Field(default_factory=dict)


class ConversationKnowledgeSource(BaseModel):
    id: str | None
    title: str | None
    status: str | None
    quality_score: float | None
    source_type: str | None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class ConversationInterpretResponse(BaseModel):
    reply: str
    confidence: float = Field(ge=0, le=1)
    selected_agent: str
    task: ConversationTaskDraft
    template: ConversationTemplateChoice
    knowledge_scope: dict[str, Any]
    knowledge_sources: list[ConversationKnowledgeSource]
    clarification_questions: list[str] = Field(default_factory=list)
