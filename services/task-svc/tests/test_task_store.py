"""PostgreSQL-backed TaskStore behavior."""

from __future__ import annotations

from app.schemas.tasks import TaskCreateRequest, TaskEventCreate
from app.services.task_store import TaskStore


def test_task_store_persists_lifecycle_events_and_result() -> None:
    store = TaskStore()

    task = store.create(
        TaskCreateRequest(
            task_type="pytest_store",
            goal="Persist a task through the database store.",
            input={"topic": "postgresql"},
            template="default",
            output_format="Markdown",
        )
    )

    assert task.status == "queued"
    assert [event.event_type for event in task.events] == ["task.created"]

    with_event = store.add_event(
        task.id,
        TaskEventCreate(
            event_type="task.started",
            message="The worker started.",
            data={"worker": "pytest"},
        ),
    )
    assert with_event is not None
    assert [event.event_type for event in with_event.events] == [
        "task.created",
        "task.started",
    ]

    completed = store.update(
        task.id,
        status="succeeded",
        result={"markdown": "# Done", "summary": "ok"},
        event=TaskEventCreate(
            event_type="task.completed",
            message="The worker finished.",
        ),
    )

    assert completed is not None
    assert completed.status == "succeeded"
    assert completed.result == {"markdown": "# Done", "summary": "ok"}
    assert [event.event_type for event in completed.events] == [
        "task.created",
        "task.started",
        "task.completed",
    ]

    loaded = store.get(task.id)
    assert loaded is not None
    assert loaded.status == "succeeded"
    assert loaded.result == {"markdown": "# Done", "summary": "ok"}

    listed_ids = {listed_task.id for listed_task in store.list()}
    assert task.id in listed_ids


def test_task_store_does_not_move_terminal_task_back_to_running() -> None:
    store = TaskStore()
    task = store.create(
        TaskCreateRequest(
            task_type="pytest_terminal",
            goal="Keep terminal task status stable.",
        )
    )

    completed = store.update(task.id, status="succeeded")
    assert completed is not None
    assert completed.status == "succeeded"

    unchanged = store.update(task.id, status="running")
    assert unchanged is not None
    assert unchanged.status == "succeeded"


def test_task_store_cancel_records_cancelled_event() -> None:
    store = TaskStore()
    task = store.create(
        TaskCreateRequest(
            task_type="pytest_cancel",
            goal="Cancel this task.",
        )
    )

    cancelled = store.cancel(task.id)

    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert cancelled.events[-1].event_type == "task.cancelled"
