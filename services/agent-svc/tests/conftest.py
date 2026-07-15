"""Test fixtures for agent-svc."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.harness import AgentHarness  # noqa: E402
from app.main import create_app  # noqa: E402
from app.orchestrator import executors  # noqa: E402


class FakeModelClient:
    def generate(self, *, request, agent, prompt):
        return {
            "provider": "fake-model-svc",
            "model": "fake-deterministic-model",
            "markdown": f"# {agent.name} Fake Model Output\n\n{prompt}",
            "summary": f"{agent.name} generated fake {request.task_type} content.",
            "usage": {
                "prompt_tokens": len(prompt.split()) or 1,
                "completion_tokens": 5,
                "total_tokens": (len(prompt.split()) or 1) + 5,
            },
            "trace": {"agent": agent.name, "task_type": request.task_type},
        }


@pytest.fixture(autouse=True)
def fake_model_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        executors,
        "agent_harness",
        AgentHarness(model_client=FakeModelClient()),
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
