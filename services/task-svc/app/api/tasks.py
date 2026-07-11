"""Task lifecycle API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.tasks import (
    TaskCreateRequest,
    TaskEventCreate,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services.queue_publisher import task_queue_publisher
from app.services.task_store import task_store

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(request: TaskCreateRequest) -> TaskResponse:
    task = task_store.create(request)
    try:
        task = task_store.add_event(
            task.id,
            TaskEventCreate(
                event_type="task.queued",
                message="Task queued for RabbitMQ dispatch.",
            ),
        )
        task_queue_publisher.publish(
            {
                "task_id": task.id,
                "task_type": task.task_type,
                "goal": task.goal,
                "input": task.input,
                "template": task.template,
                "output_format": task.output_format,
            }
        )
    except Exception as exc:
        task = task_store.update(
            task.id,
            status="failed",
            error=str(exc),
            event=TaskEventCreate(
                event_type="task.queue_failed",
                message="Task could not be published to RabbitMQ.",
                data={"error": str(exc)},
            ),
        )
    return task.to_response()


@router.get("", response_model=list[TaskResponse])
def list_tasks() -> list[TaskResponse]:
    return [task.to_response() for task in task_store.list()]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_response()


@router.post("/{task_id}/events", response_model=TaskResponse)
def add_task_event(task_id: str, request: TaskEventCreate) -> TaskResponse:
    task = task_store.add_event(task_id, request)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_response()


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, request: TaskUpdateRequest) -> TaskResponse:
    task = task_store.update(
        task_id,
        status=request.status,
        result=request.result,
        error=request.error,
        event=request.event,
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_response()


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: str) -> TaskResponse:
    task = task_store.cancel(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task.to_response()
