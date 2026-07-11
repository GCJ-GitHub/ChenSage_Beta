"""In-memory task store for the phase 1 execution loop.

The API shape is intentionally close to a future database-backed repository so
PostgreSQL can replace this store without changing worker or frontend calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4

from app.schemas.tasks import (
    TaskCreateRequest,
    TaskEventCreate,
    TaskEventResponse,
    TaskResponse,
    TaskStatus,
)

TERMINAL_STATUSES: set[TaskStatus] = {"succeeded", "failed", "cancelled", "expired"}


@dataclass(slots=True)
class TaskEventRecord:
    id: str
    task_id: str
    event_type: str
    message: str
    data: dict[str, Any]
    created_at: datetime

    def to_response(self) -> TaskEventResponse:
        return TaskEventResponse(
            id=self.id,
            task_id=self.task_id,
            event_type=self.event_type,
            message=self.message,
            data=self.data,
            created_at=self.created_at,
        )


@dataclass(slots=True)
class TaskRecord:
    id: str
    task_type: str
    goal: str
    input: dict[str, Any]
    template: str | None
    output_format: str | None
    status: TaskStatus
    result: dict[str, Any] | None
    error: str | None
    events: list[TaskEventRecord] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_response(self) -> TaskResponse:
        return TaskResponse(
            id=self.id,
            task_type=self.task_type,
            goal=self.goal,
            input=self.input,
            template=self.template,
            output_format=self.output_format,
            status=self.status,
            result=self.result,
            error=self.error,
            events=[event.to_response() for event in self.events],
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, request: TaskCreateRequest) -> TaskRecord:
        now = datetime.now(UTC)
        task = TaskRecord(
            id=str(uuid4()),
            task_type=request.task_type,
            goal=request.goal,
            input=request.input,
            template=request.template,
            output_format=request.output_format,
            status="queued",
            result=None,
            error=None,
            created_at=now,
            updated_at=now,
        )
        task.events.append(
            self._new_event(
                task.id,
                TaskEventCreate(
                    event_type="task.created",
                    message="Task created and ready to publish to the worker queue.",
                ),
            )
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def list(self) -> list[TaskRecord]:
        with self._lock:
            return sorted(self._tasks.values(), key=lambda task: task.created_at, reverse=True)

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            return self._tasks.get(task_id)

    def add_event(self, task_id: str, event: TaskEventCreate) -> TaskRecord | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.events.append(self._new_event(task_id, event))
            task.updated_at = datetime.now(UTC)
            return task

    def update(
        self,
        task_id: str,
        *,
        status: TaskStatus | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        event: TaskEventCreate | None = None,
    ) -> TaskRecord | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if task.status in TERMINAL_STATUSES and status not in {None, task.status}:
                return task
            if status is not None:
                task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            if event is not None:
                task.events.append(self._new_event(task_id, event))
            task.updated_at = datetime.now(UTC)
            return task

    def cancel(self, task_id: str) -> TaskRecord | None:
        return self.update(
            task_id,
            status="cancelled",
            event=TaskEventCreate(
                event_type="task.cancelled",
                message="Task was cancelled by the user.",
            ),
        )

    @staticmethod
    def _new_event(task_id: str, event: TaskEventCreate) -> TaskEventRecord:
        return TaskEventRecord(
            id=str(uuid4()),
            task_id=task_id,
            event_type=event.event_type,
            message=event.message,
            data=event.data,
            created_at=datetime.now(UTC),
        )


task_store = TaskStore()

