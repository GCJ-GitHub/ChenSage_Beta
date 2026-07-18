"""Agent harness and loop-engine behavior."""

from __future__ import annotations

from app.context_engine import KnowledgeContext
from app.harness import AgentDefinition, AgentHarness
from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep


class FakeModelClient:
    def generate(self, *, request, agent, prompt):
        return {
            "provider": "fake-model-svc",
            "model": "fake-deterministic-model",
            "markdown": "# Harness",
            "summary": "Harness completed.",
            "usage": {"prompt_tokens": 2, "completion_tokens": 2, "total_tokens": 4},
            "trace": {"agent": agent.name, "task_type": request.task_type},
        }


class EmptyContextEngine:
    def retrieve(self, request: AgentExecutionRequest) -> KnowledgeContext:
        return KnowledgeContext(task_type=request.task_type)


def test_agent_harness_returns_plan_act_observe_finalize_trace() -> None:
    harness = AgentHarness(
        model_client=FakeModelClient(),
        context_engine=EmptyContextEngine(),
    )
    response = harness.run(
        request=AgentExecutionRequest(
            task_id="pytest-harness",
            task_type="content",
            goal="Validate harness trace.",
        ),
        agent=AgentDefinition(name="content-agent", role="Draft content."),
        executor="content-executor",
        plan=[
            AgentExecutionStep(name="content-agent.read_goal", detail="Read the goal."),
            AgentExecutionStep(name="content-agent.write_outline", detail="Write the outline."),
        ],
    )

    phases = [step.phase for step in response.trace]
    assert phases == [
        "plan",
        "act",
        "observe",
        "act",
        "observe",
        "observe",
        "act",
        "observe",
        "finalize",
    ]
    assert response.trace[5].name == "context.knowledge_retrieved"
    assert response.result.duration_ms == sum(step.duration_ms for step in response.trace)
    assert response.result.trace == response.trace
    assert response.events == response.trace
    assert response.result.provider == "fake-model-svc"
    assert response.result.usage["total_tokens"] == 4


def test_internal_execute_response_contains_trace(client) -> None:
    response = client.post(
        "/internal/execute",
        json={
            "task_id": "pytest-trace-api",
            "task_type": "content",
            "goal": "Return trace from API.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["trace"][0]["phase"] == "plan"
    assert body["trace"][-1]["phase"] == "finalize"
    assert body["result"]["trace"] == body["trace"]
    assert body["result"]["duration_ms"] > 0
    assert body["result"]["provider"] == "fake-model-svc"
