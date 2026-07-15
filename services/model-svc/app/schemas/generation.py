"""Schemas for internal deterministic model generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModelGenerateRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=80)
    agent: str = Field(min_length=1, max_length=120)
    task_type: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=5000)
    prompt: str = Field(min_length=1, max_length=12000)
    output_format: str | None = Field(default="Markdown", max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ModelGenerateResponse(BaseModel):
    provider: str
    model: str
    markdown: str
    summary: str
    usage: ModelUsage
    trace: dict[str, Any] = Field(default_factory=dict)
