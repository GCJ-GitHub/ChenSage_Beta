"""Internal agent execution API behavior."""

from __future__ import annotations

import pytest
from app.orchestrator.executors import execute_task, get_executor
from app.schemas.execution import AgentExecutionRequest


@pytest.mark.parametrize(
    ("task_type", "executor_name", "heading"),
    [
        ("content", "content-executor", "# content-agent Fake Model Output"),
        ("research", "research-executor", "# research-agent Fake Model Output"),
        ("arxiv", "arxiv-executor", "# arxiv-agent Fake Model Output"),
        ("interview", "interview-executor", "# interview-agent Fake Model Output"),
        ("file", "file-executor", "# file-agent Fake Model Output"),
    ],
)
def test_execute_task_uses_registered_executor(
    task_type: str,
    executor_name: str,
    heading: str,
) -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-task",
            task_type=task_type,
            goal="Validate executor routing.",
            template="pytest",
            output_format="Markdown",
        )
    )

    assert response.executor == executor_name
    assert response.result.executor == executor_name
    assert response.result.task_type == task_type
    assert heading in response.result.markdown
    assert response.events
    assert response.trace
    assert response.trace[0].phase == "plan"
    assert response.trace[-1].phase == "finalize"
    assert any(step.name == "context.knowledge_retrieved" for step in response.trace)
    assert response.result.provider == "fake-model-svc"
    assert response.result.usage["total_tokens"] > 0


def test_execute_task_injects_knowledge_context_into_prompt_and_artifacts() -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-knowledge-context",
            task_type="content_generation",
            goal="Use retrieved knowledge while drafting.",
        )
    )

    assert "Knowledge context:" in response.result.markdown
    assert "Fake content knowledge" in response.result.markdown
    assert "Use a concise structure and keep source references visible." in response.result.markdown
    knowledge_artifact = next(
        artifact
        for artifact in response.result.artifacts
        if artifact["type"] == "knowledge_context"
    )
    assert knowledge_artifact["task_type"] == "content"
    assert knowledge_artifact["item_count"] == 1


def test_content_generation_includes_phase6_content_spec() -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-content-generation",
            task_type="content_generation",
            goal="写一篇公众号文章介绍阶段 6。",
            input={
                "content_type": "公众号文章",
                "audience": "产品用户",
                "tone": "清晰",
                "length": "约 800 字",
            },
        )
    )

    assert response.executor == "content-executor"
    assert response.result.steps[0].name == "content-agent.plan_outline"
    artifact = response.result.artifacts[0]
    assert artifact["type"] == "content_task_spec"
    assert artifact["mode"] == "generation"
    assert artifact["content_type"] == "公众号文章"
    assert artifact["audience"] == "产品用户"
    assert "期望长度：约 800 字" in response.result.markdown


def test_content_rewrite_uses_rewrite_plan_and_artifact() -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-content-rewrite",
            task_type="content_rewrite",
            goal="把这段内容改得更清晰。",
            input={
                "content_type": "公众号文章",
                "generated_content": "这是一段需要改写的原文。",
                "rewrite_instruction": "保留原意，结构更清楚。",
                "audience": "内部团队",
                "tone": "专业",
            },
        )
    )

    assert response.result.steps[0].name == "content-agent.read_source"
    assert response.result.steps[1].name == "content-agent.rewrite"
    artifact = response.result.artifacts[0]
    assert artifact["type"] == "content_task_spec"
    assert artifact["mode"] == "rewrite"
    assert artifact["source_text_preview"] == "这是一段需要改写的原文。"
    assert "Template: content.rewrite" in response.result.markdown


@pytest.mark.parametrize(
    "task_type",
    ["content_generation", "content_rewrite", "essay", "novel", "standup_script"],
)
def test_content_aliases_reuse_content_executor(task_type: str) -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-alias",
            task_type=task_type,
            goal="Write content.",
        )
    )

    assert response.executor == "content-executor"
    assert response.result.task_type == task_type
    assert "content-agent Fake Model Output" in response.result.markdown


def test_unknown_task_type_uses_generic_executor() -> None:
    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-fallback",
            task_type="custom_future_task",
            goal="Handle safely.",
        )
    )

    assert response.executor == "generic-executor"
    assert response.result.task_type == "custom_future_task"
    assert "planner-agent Fake Model Output" in response.result.markdown


def test_get_executor_returns_generic_fallback() -> None:
    request = AgentExecutionRequest(
        task_id="pytest-fallback",
        task_type="missing-task-type",
        goal="Fallback.",
    )
    assert get_executor("missing-task-type")(request).executor == "generic-executor"


def test_internal_execute_endpoint(client) -> None:
    response = client.post(
        "/internal/execute",
        json={
            "task_id": "pytest-api",
            "task_type": "research_report",
            "goal": "Build a deterministic research plan.",
            "input": {"topic": "agent-svc"},
            "output_format": "Markdown",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "pytest-api"
    assert body["executor"] == "research-executor"
    assert body["status"] == "succeeded"
    assert body["result"]["executor"] == "research-executor"
    assert body["events"]
    assert body["trace"][0]["phase"] == "plan"
    assert body["result"]["duration_ms"] > 0
    assert body["result"]["provider"] == "fake-model-svc"
