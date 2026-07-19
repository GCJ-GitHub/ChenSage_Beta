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


class FakeEvalClient:
    def evaluate(self, *, request, generated_content, context):
        del generated_content
        return {
            "type": "eval_report",
            "task_id": request.task_id,
            "task_type": request.task_type,
            "overall_score": 4.2,
            "scores": {
                "factual_accuracy": 4,
                "structure_integrity": 5,
                "style_match": 4,
                "platform_fit": 4,
                "usability": 4,
            },
            "score_reasons": {
                "factual_accuracy": "Fake evaluation saw reusable knowledge context.",
                "structure_integrity": "Fake evaluation saw Markdown structure.",
                "style_match": "Fake evaluation saw tone context.",
                "platform_fit": "Fake evaluation saw content type.",
                "usability": "Fake evaluation marks this as usable.",
            },
            "issue_locations": [
                {
                    "location": "结果尾部",
                    "issue": "Prompt Snapshot is visible.",
                    "severity": "low",
                    "suggestion": "Hide debug content before export.",
                }
            ],
            "revision_advice": ["Add one concrete example."],
            "usable_highlights": ["Markdown structure is present."],
            "source_risks": ["Fake source risk."],
            "learning_candidates": [
                {
                    "kind": "structure_pattern",
                    "summary": "Keep structured Markdown.",
                    "evidence": str(context.get("content_task_spec") or {}),
                    "confidence": 0.8,
                    "status": "candidate",
                }
            ],
            "evaluator": "fake-eval-svc",
        }


@pytest.fixture(autouse=True)
def fake_model_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        executors,
        "agent_harness",
        AgentHarness(
            model_client=FakeModelClient(),
            eval_client=FakeEvalClient(),
            context_engine=KnowledgeContextEngine(client=FakeKnowledgeBaseClient()),
        ),
    )


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
