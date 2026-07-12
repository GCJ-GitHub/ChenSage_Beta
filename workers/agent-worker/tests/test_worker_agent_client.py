"""agent-worker integration boundary with agent-svc."""

from __future__ import annotations

from typing import Any

from app.main import handle_message


class RecordingTaskClient:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []

    def update(
        self,
        task_id: str,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        event_type: str,
        message: str,
    ) -> None:
        self.updates.append(
            {
                "task_id": task_id,
                "status": status,
                "result": result,
                "error": error,
                "event_type": event_type,
                "message": message,
            }
        )

    def event(
        self,
        task_id: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(
            {
                "task_id": task_id,
                "event_type": event_type,
                "message": message,
                "data": data or {},
            }
        )


class StubAgentClient:
    def execute(self, message: dict[str, Any]) -> dict[str, Any]:
        return {
            "task_id": message["task_id"],
            "task_type": message["task_type"],
            "executor": "content-executor",
            "status": "succeeded",
            "result": {
                "format": message["output_format"],
                "markdown": "# Content Draft",
                "summary": "agent-svc completed content execution.",
                "executor": "content-executor",
                "task_type": message["task_type"],
                "steps": [],
                "artifacts": [],
            },
            "events": [],
        }


def test_handle_message_calls_agent_svc_and_writes_back_result() -> None:
    task_client = RecordingTaskClient()
    agent_client = StubAgentClient()

    handle_message(
        task_client,
        agent_client,
        {
            "task_id": "pytest-task",
            "task_type": "content",
            "goal": "Write a draft.",
            "input": {},
            "template": "default",
            "output_format": "Markdown",
        },
    )

    assert [update["status"] for update in task_client.updates] == ["running", "succeeded"]
    assert task_client.events[0]["event_type"] == "task.executor_selected"
    assert task_client.events[0]["data"]["service"] == "agent-svc"
    assert task_client.updates[-1]["result"]["executor"] == "content-executor"
