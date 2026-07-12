"""Task lifecycle API behavior."""

from __future__ import annotations

from typing import Any

import pytest
from app.api import tasks as tasks_api


class RecordingPublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def publish(self, message: dict[str, Any]) -> None:
        self.messages.append(message)


@pytest.fixture
def publisher(monkeypatch: pytest.MonkeyPatch) -> RecordingPublisher:
    publisher = RecordingPublisher()
    monkeypatch.setattr(tasks_api, "task_queue_publisher", publisher)
    return publisher


def test_create_task_persists_and_publishes_message(client, publisher: RecordingPublisher) -> None:
    response = client.post(
        "/tasks",
        json={
            "task_type": "pytest_api_create",
            "goal": "Create a task from the API.",
            "input": {"topic": "api"},
            "template": "concise",
            "output_format": "Markdown",
        },
    )

    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "queued"
    assert [event["event_type"] for event in task["events"]] == [
        "task.created",
        "task.queued",
    ]
    assert publisher.messages == [
        {
            "task_id": task["id"],
            "task_type": "pytest_api_create",
            "goal": "Create a task from the API.",
            "input": {"topic": "api"},
            "template": "concise",
            "output_format": "Markdown",
        }
    ]

    detail = client.get(f"/tasks/{task['id']}")
    assert detail.status_code == 200
    assert detail.json()["id"] == task["id"]

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    assert task["id"] in {listed_task["id"] for listed_task in list_response.json()}


def test_update_event_and_cancel_task_through_api(client, publisher: RecordingPublisher) -> None:
    del publisher
    created = client.post(
        "/tasks",
        json={"task_type": "pytest_api_update", "goal": "Exercise API updates."},
    ).json()
    task_id = created["id"]

    event_response = client.post(
        f"/tasks/{task_id}/events",
        json={
            "event_type": "task.note",
            "message": "A progress note.",
            "data": {"step": 1},
        },
    )
    assert event_response.status_code == 200
    assert event_response.json()["events"][-1]["event_type"] == "task.note"

    patch_response = client.patch(
        f"/tasks/{task_id}",
        json={
            "status": "running",
            "event": {
                "event_type": "task.started",
                "message": "Started by test.",
                "data": {},
            },
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "running"

    cancel_response = client.post(f"/tasks/{task_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"
    assert cancel_response.json()["events"][-1]["event_type"] == "task.cancelled"


def test_missing_task_returns_404(client) -> None:
    assert client.get("/tasks/missing-task-id").status_code == 404
    event_response = client.post(
        "/tasks/missing-task-id/events",
        json={"event_type": "x", "message": "x"},
    )
    assert event_response.status_code == 404
    assert client.patch("/tasks/missing-task-id", json={"status": "running"}).status_code == 404
    assert client.post("/tasks/missing-task-id/cancel").status_code == 404
