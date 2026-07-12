"""Agent harness and loop-engine behavior."""

from __future__ import annotations

from app.harness import AgentDefinition, AgentHarness
from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep


def test_agent_harness_returns_plan_act_observe_finalize_trace() -> None:
    harness = AgentHarness()
    response = harness.run(
        request=AgentExecutionRequest(
            task_id="pytest-harness",
            task_type="content",
            goal="Validate harness trace.",
        ),
        agent=AgentDefinition(name="content-agent", role="Draft content."),
        executor="content-executor",
        summary="Harness completed.",
        markdown="# Harness",
        plan=[
            AgentExecutionStep(name="content-agent.read_goal", detail="Read the goal."),
            AgentExecutionStep(name="content-agent.write_outline", detail="Write the outline."),
        ],
    )

    phases = [step.phase for step in response.trace]
    assert phases == ["plan", "act", "observe", "act", "observe", "finalize"]
    assert response.result.duration_ms == sum(step.duration_ms for step in response.trace)
    assert response.result.trace == response.trace
    assert response.events == response.trace


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
