"""Knowledge context engine behavior."""

from __future__ import annotations

from app.context_engine.knowledge import KnowledgeContextEngine, normalize_knowledge_task_type
from app.schemas.execution import AgentExecutionRequest


class FailingKnowledgeBaseClient:
    def search(self, *, task_type, status=None, tags=None, limit=3):
        del task_type, status, tags, limit
        raise RuntimeError("knowledge service unavailable")


def test_context_engine_normalizes_task_type_aliases() -> None:
    assert normalize_knowledge_task_type("content_generation") == "content"
    assert normalize_knowledge_task_type("research_report") == "research"
    assert normalize_knowledge_task_type("arxiv_daily") == "arxiv"
    assert normalize_knowledge_task_type("mock_interview") == "interview"


def test_context_engine_returns_failed_trace_step_when_retrieval_fails() -> None:
    context = KnowledgeContextEngine(client=FailingKnowledgeBaseClient()).retrieve(
        AgentExecutionRequest(
            task_id="pytest-context-failure",
            task_type="content_generation",
            goal="Keep task running.",
        )
    )

    step = context.to_trace_step()
    assert context.items == []
    assert context.error == "knowledge service unavailable"
    assert step.name == "context.knowledge_unavailable"
    assert step.status == "failed"
