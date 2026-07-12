"""Deterministic executors owned by agent-svc orchestration."""

from __future__ import annotations

from collections.abc import Callable

from app.schemas.execution import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentExecutionResult,
    AgentExecutionStep,
)

TaskExecutor = Callable[[AgentExecutionRequest], AgentExecutionResponse]


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
    markdown = _markdown_document(
        "Content Draft",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Template", request.template or "default content template"),
            ("Next integration", "Replace deterministic drafting with content-agent + model-svc."),
        ],
    )
    return _response(
        request,
        executor="content-executor",
        summary="agent-svc produced a deterministic content draft outline.",
        markdown=markdown,
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
    markdown = _markdown_document(
        "Research Brief",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Source policy", "Collect sources through tool-registry with audit metadata."),
            ("Next integration", "Replace deterministic planning with research-agent tools."),
        ],
    )
    return _response(
        request,
        executor="research-executor",
        summary="agent-svc produced a deterministic research plan.",
        markdown=markdown,
        steps=steps,
    )


def arxiv_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="research-agent", detail="Load research direction and keywords."),
        AgentExecutionStep(name="tool-registry", detail="Prepare arXiv search tool call."),
        AgentExecutionStep(name="critic-agent", detail="Prepare relevance filtering."),
    ]
    markdown = _markdown_document(
        "arXiv Daily Brief",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Paper selection", "Load categories, date range, and max paper count."),
            ("Next integration", "Replace deterministic outline with arXiv tooling."),
        ],
    )
    return _response(
        request,
        executor="arxiv-executor",
        summary="agent-svc produced a deterministic arXiv daily brief outline.",
        markdown=markdown,
        steps=steps,
    )


def interview_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="file-svc", detail="Prepare resume parsing boundary."),
        AgentExecutionStep(name="interview-agent", detail="Generate role-specific question plan."),
        AgentExecutionStep(name="eval-svc", detail="Prepare answer scoring report."),
    ]
    markdown = _markdown_document(
        "Interview Prep",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Resume flow", "Parse evidence before generating role-specific questions."),
            ("Next integration", "Replace deterministic outline with interview-agent."),
        ],
    )
    return _response(
        request,
        executor="interview-executor",
        summary="agent-svc produced a deterministic interview prep outline.",
        markdown=markdown,
        steps=steps,
    )


def file_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="file-svc", detail="Read file metadata and object keys."),
        AgentExecutionStep(name="tool-registry", detail="Select parser for the file type."),
        AgentExecutionStep(name="context-engine", detail="Extract reusable context."),
    ]
    markdown = _markdown_document(
        "File Analysis",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Storage flow", "Read file metadata and object keys from file-svc."),
            ("Next integration", "Replace deterministic outline with file-agent."),
        ],
    )
    return _response(
        request,
        executor="file-executor",
        summary="agent-svc produced a deterministic file analysis outline.",
        markdown=markdown,
        steps=steps,
    )


def generic_executor(request: AgentExecutionRequest) -> AgentExecutionResponse:
    steps = [
        AgentExecutionStep(name="planner-agent", detail="Route unknown task type safely."),
        AgentExecutionStep(name="agent-svc", detail="Return deterministic fallback result."),
    ]
    markdown = _markdown_document(
        "Generic Task Result",
        [
            ("Task type", request.task_type),
            ("Goal", request.goal),
            ("Next integration", "Add a dedicated executor or planner-agent route."),
        ],
    )
    return _response(
        request,
        executor="generic-executor",
        summary="agent-svc completed the task with the generic deterministic executor.",
        markdown=markdown,
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
    executor: str,
    summary: str,
    markdown: str,
    steps: list[AgentExecutionStep],
) -> AgentExecutionResponse:
    result = AgentExecutionResult(
        format=request.output_format or "Markdown",
        markdown=markdown,
        summary=summary,
        executor=executor,
        task_type=request.task_type,
        steps=steps,
    )
    return AgentExecutionResponse(
        task_id=request.task_id,
        task_type=request.task_type,
        executor=executor,
        result=result,
        events=steps,
    )


def _markdown_document(title: str, rows: list[tuple[str, str]]) -> str:
    lines = [f"# {title}", ""]
    lines.extend(f"- {label}: {value}" for label, value in rows)
    return "\n".join(lines)
