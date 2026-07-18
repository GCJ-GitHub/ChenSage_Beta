"""Schemas for prompt template registry APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PromptVariableType = Literal["string", "array", "number", "boolean", "object"]


class PromptVariableDefinition(BaseModel):
    type: PromptVariableType = "string"
    required: bool = False
    description: str | None = None


class PromptTemplateResponse(BaseModel):
    id: str
    name: str
    task_type: str
    category: str
    version: str
    variables: dict[str, PromptVariableDefinition] = Field(default_factory=dict)
    template: str
    source_path: str


class PromptTemplateRenderResponse(BaseModel):
    template_id: str
    rendered: str
    missing_variables: list[str] = Field(default_factory=list)
