"""Pydantic schemas for task lifecycle APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TaskStatus = Literal[
    "queued",
    "running",
    "waiting_approval",
    "succeeded",
    "failed",
    "cancelled",
    "expired",
]


class TaskCreateRequest(BaseModel):
    task_type: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=5000)
    input: dict[str, Any] = Field(default_factory=dict)
    template: str | None = Field(default=None, max_length=120)
    output_format: str | None = Field(default="Markdown", max_length=80)


class TaskEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=1, max_length=1000)
    data: dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    status: TaskStatus | None = None
    result: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=2000)
    event: TaskEventCreate | None = None


class TaskEventResponse(BaseModel):
    id: str
    task_id: str
    event_type: str
    message: str
    data: dict[str, Any]
    created_at: datetime


class TaskResponse(BaseModel):
    id: str
    task_type: str
    goal: str
    input: dict[str, Any]
    template: str | None
    output_format: str | None
    status: TaskStatus
    result: dict[str, Any] | None
    error: str | None
    events: list[TaskEventResponse]
    created_at: datetime
    updated_at: datetime

