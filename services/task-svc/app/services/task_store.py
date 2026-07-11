"""PostgreSQL-backed task store for the phase 1 execution loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import session_scope
from app.models.tasks import TaskEventModel, TaskModel, TaskResultModel
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_response(self) -> TaskResponse:
        if self.created_at is None or self.updated_at is None:
            raise ValueError("Task timestamps must be loaded before creating a response")
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
    def create(self, request: TaskCreateRequest) -> TaskRecord:
        task_id = str(uuid4())
        with session_scope() as session:
            task = TaskModel(
                id=task_id,
                task_type=request.task_type,
                goal=request.goal,
                input=request.input,
                template=request.template,
                output_format=request.output_format,
                status="queued",
            )
            task.events.append(
                self._new_event(
                    task_id,
                    TaskEventCreate(
                        event_type="task.created",
                        message="Task created and ready to publish to the worker queue.",
                    ),
                )
            )
            session.add(task)
            session.flush()
            session.refresh(task)
            return self._to_record(task)

    def list(self) -> list[TaskRecord]:
        with session_scope() as session:
            tasks = (
                session.execute(
                    select(TaskModel)
                    .options(joinedload(TaskModel.events), joinedload(TaskModel.result))
                    .order_by(TaskModel.created_at.desc())
                )
                .unique()
                .scalars()
                .all()
            )
            return [self._to_record(task) for task in tasks]

    def get(self, task_id: str) -> TaskRecord | None:
        with session_scope() as session:
            task = self._get_model(session, task_id)
            if task is None:
                return None
            return self._to_record(task)

    def add_event(self, task_id: str, event: TaskEventCreate) -> TaskRecord | None:
        with session_scope() as session:
            task = self._get_model(session, task_id)
            if task is None:
                return None
            task.events.append(self._new_event(task_id, event))
            task.updated_at = datetime.now(UTC)
            session.flush()
            session.refresh(task)
            return self._to_record(task)

    def update(
        self,
        task_id: str,
        *,
        status: TaskStatus | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        event: TaskEventCreate | None = None,
    ) -> TaskRecord | None:
        with session_scope() as session:
            task = self._get_model(session, task_id)
            if task is None:
                return None
            if task.status in TERMINAL_STATUSES and status not in {None, task.status}:
                return self._to_record(task)
            if status is not None:
                task.status = status
            if error is not None:
                task.error = error
            if result is not None:
                if task.result is None:
                    task.result = TaskResultModel(id=str(uuid4()), task_id=task_id, data=result)
                else:
                    task.result.data = result
            if event is not None:
                task.events.append(self._new_event(task_id, event))
            task.updated_at = datetime.now(UTC)
            session.flush()
            session.refresh(task)
            return self._to_record(task)

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
    def _get_model(session, task_id: str) -> TaskModel | None:
        return (
            session.execute(
                select(TaskModel)
                .options(joinedload(TaskModel.events), joinedload(TaskModel.result))
                .where(TaskModel.id == task_id)
            )
            .unique()
            .scalar_one_or_none()
        )

    @staticmethod
    def _new_event(task_id: str, event: TaskEventCreate) -> TaskEventModel:
        return TaskEventModel(
            id=str(uuid4()),
            task_id=task_id,
            event_type=event.event_type,
            message=event.message,
            data=event.data,
        )

    @staticmethod
    def _to_record(task: TaskModel) -> TaskRecord:
        return TaskRecord(
            id=task.id,
            task_type=task.task_type,
            goal=task.goal,
            input=task.input,
            template=task.template,
            output_format=task.output_format,
            status=task.status,
            result=task.result.data if task.result is not None else None,
            error=task.error,
            events=[
                TaskEventRecord(
                    id=event.id,
                    task_id=event.task_id,
                    event_type=event.event_type,
                    message=event.message,
                    data=event.data,
                    created_at=event.created_at,
                )
                for event in task.events
            ],
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


task_store = TaskStore()
