"""Deterministic executors owned by agent-svc orchestration."""

from __future__ import annotations

from collections.abc import Callable

from app.agents import (
    ARXIV_AGENT,
    CONTENT_AGENT,
    FILE_AGENT,
    INTERVIEW_AGENT,
    PLANNER_AGENT,
    RESEARCH_AGENT,
)
from app.harness import AgentDefinition, AgentHarness
from app.schemas.execution import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentExecutionStep,
)

TaskExecutor = Callable[[AgentExecutionRequest], AgentExecutionResponse]
agent_harness = AgentHarness()


def execute_task(request: AgentExecutionRequest) -> AgentExecutionResponse:
    return get_executor(request.task_type)(request)


def get_executor(task_type: str) -> TaskExecutor:
    return EXECUTOR_REGISTRY.get(task_type, generic_executor)


def content_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="content-agent", detail="Read goal, template, and output format."),
        AgentExecutionStep(name="critic-agent", detail="Prepare a later quality review pass."),
        AgentExecutionStep(name="eval-svc", detail="Reserve structured feedback for phase 2."),
    ]
    return _response(
        request,
        agent=CONTENT_AGENT,
        executor="content-executor",
        steps=steps,
    )


def research_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="policy-svc", detail="Check source and external access policy."),
        AgentExecutionStep(
            name="research-agent",
            detail="Plan source collection and deduplication.",
        ),
        AgentExecutionStep(name="content-agent", detail="Prepare report synthesis."),
    ]
    return _response(
        request,
        agent=RESEARCH_AGENT,
        executor="research-executor",
        steps=steps,
    )


def arxiv_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="research-agent", detail="Load research direction and keywords."),
        AgentExecutionStep(name="tool-registry", detail="Prepare arXiv search tool call."),
        AgentExecutionStep(name="critic-agent", detail="Prepare relevance filtering."),
    ]
    return _response(
        request,
        agent=ARXIV_AGENT,
        executor="arxiv-executor",
        steps=steps,
    )


def interview_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="file-svc", detail="Prepare resume parsing boundary."),
        AgentExecutionStep(name="interview-agent", detail="Generate role-specific question plan."),
        AgentExecutionStep(name="eval-svc", detail="Prepare answer scoring report."),
    ]
    return _response(
        request,
        agent=INTERVIEW_AGENT,
        executor="interview-executor",
        steps=steps,
    )


def file_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="file-svc", detail="Read file metadata and object keys."),
        AgentExecutionStep(name="tool-registry", detail="Select parser for the file type."),
        AgentExecutionStep(name="context-engine", detail="Extract reusable context."),
    ]
    return _response(
        request,
        agent=FILE_AGENT,
        executor="file-executor",
        steps=steps,
    )


def generic_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="planner-agent", detail="Route unknown task type safely."),
        AgentExecutionStep(name="agent-svc", detail="Return deterministic fallback result."),
    ]
    return _response(
        request,
        agent=PLANNER_AGENT,
        executor="generic-executor",
        steps=steps,
    )


EXECUTOR_REGISTRY: dict[str, TaskExecutor] = {
    "content": content_executor,
    "content_generation": content_executor,
    "content_rewrite": content_executor,
    "essay": content_executor,
    "novel": content_executor,
    "speech_script": content_executor,
    "standup_script": content_executor,
    "research": research_executor,
    "research_report": research_executor,
    "information_collection": research_executor,
    "arxiv": arxiv_executor,
    "arxiv_daily": arxiv_executor,
    "interview": interview_executor,
    "mock_interview": interview_executor,
    "file": file_executor,
    "file_analysis": file_executor,
}


def _response(
    request: AgentExecutionRequest,
    *,
    agent: AgentDefinition,
    executor: str,
    steps: list[AgentExecutionStep],
) -> AgentExecutionResponse:
    return agent_harness.run(
        request=request,
        agent=agent,
        executor=executor,
        plan=steps,
    )
