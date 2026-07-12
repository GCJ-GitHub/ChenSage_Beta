"""Schemas for internal agent execution requests."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentExecutionRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=80)
    task_type: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=5000)
    input: dict[str, Any] = Field(default_factory=dict)
    template: str | None = Field(default=None, max_length=120)
    output_format: str | None = Field(default="Markdown", max_length=80)


class AgentExecutionStep(BaseModel):
    name: str
    detail: str
    phase: Literal["plan", "act", "observe", "finalize"] = "act"
    agent: str | None = None
    status: Literal["succeeded", "failed"] = "succeeded"
    duration_ms: int = Field(default=0, ge=0)
    data: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResult(BaseModel):
    format: str
    markdown: str
    summary: str
    executor: str
    task_type: str
    steps: list[AgentExecutionStep]
    trace: list[AgentExecutionStep]
    duration_ms: int = Field(default=0, ge=0)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)


class AgentExecutionResponse(BaseModel):
    task_id: str
    task_type: str
    executor: str
    status: Literal["succeeded"] = "succeeded"
    result: AgentExecutionResult
    events: list[AgentExecutionStep]
    trace: list[AgentExecutionStep]
