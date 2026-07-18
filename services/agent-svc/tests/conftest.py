"""Test fixtures for agent-svc."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.context_engine import KnowledgeContextEngine  # noqa: E402
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


class FakeKnowledgeBaseClient:
    def search(self, *, task_type, status=None, tags=None, limit=3):
        del status, tags
        return [
            {
                "id": f"fake-knowledge-{task_type}",
                "title": f"Fake {task_type} knowledge",
                "summary": "A reusable knowledge item selected for the current task type.",
                "task_type": task_type,
                "source_type": "generated_content",
                "status": "active",
                "quality_score": 0.91,
                "tags": [task_type, "pytest"],
                "sources": [
                    {
                        "id": "fake-source",
                        "title": "Fake source",
                        "source_type": "task_result",
                        "uri": "task://fake-knowledge",
                        "summary": "A fake source for agent-svc tests.",
                    }
                ],
                "chunks": [
                    {
                        "id": "fake-chunk",
                        "text": "Use a concise structure and keep source references visible.",
                        "ordinal": 0,
                    }
                ],
            }
        ][:limit]


@pytest.fixture(autouse=True)
def fake_model_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        executors,
        "agent_harness",
        AgentHarness(
            model_client=FakeModelClient(),
            context_engine=KnowledgeContextEngine(client=FakeKnowledgeBaseClient()),
        ),
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
