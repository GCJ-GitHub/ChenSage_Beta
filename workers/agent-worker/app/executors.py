"""Deterministic task executors for the phase 1 worker loop."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

TaskMessage = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    executor: str
    task_type: str
    summary: str
    markdown: str
    output_format: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "format": self.output_format,
            "markdown": self.markdown,
            "summary": self.summary,
            "executor": self.executor,
            "task_type": self.task_type,
            "artifacts": [],
        }


TaskExecutor = Callable[[TaskMessage], TaskExecutionResult]


def execute_task(message: TaskMessage) -> TaskExecutionResult:
    return get_executor(str(message.get("task_type", "")))(message)


def get_executor(task_type: str) -> TaskExecutor:
    return EXECUTOR_REGISTRY.get(task_type, generic_executor)


def content_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    template = message.get("template") or "default content template"
    markdown = _markdown_document(
        "Content Draft",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Template", str(template)),
            (
                "Draft direction",
                "Produce a clear first draft, then route through critic-agent and eval-svc.",
            ),
            ("Next integration", "Replace this deterministic executor with content-agent."),
        ],
    )
    return TaskExecutionResult(
        executor="content-executor",
        task_type=task_type,
        summary="Content executor produced a deterministic draft outline.",
        markdown=markdown,
        output_format=_output_format(message),
    )


def research_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    markdown = _markdown_document(
        "Research Brief",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Source policy", "Collect sources through tool-registry with audit metadata."),
            ("Synthesis plan", "Deduplicate findings, preserve citations, and draft a report."),
            ("Next integration", "Replace this deterministic executor with research-agent."),
        ],
    )
    return TaskExecutionResult(
        executor="research-executor",
        task_type=task_type,
        summary="Research executor produced a deterministic research plan.",
        markdown=markdown,
        output_format=_output_format(message),
    )


def arxiv_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    markdown = _markdown_document(
        "arXiv Daily Brief",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Paper selection", "Load categories, keywords, date range, and max paper count."),
            ("Review flow", "Rank papers, summarize contributions, and mark follow-up reads."),
            ("Next integration", "Replace this deterministic executor with arXiv tooling."),
        ],
    )
    return TaskExecutionResult(
        executor="arxiv-executor",
        task_type=task_type,
        summary="arXiv executor produced a deterministic daily brief outline.",
        markdown=markdown,
        output_format=_output_format(message),
    )


def interview_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    markdown = _markdown_document(
        "Interview Prep",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Resume flow", "Parse resume evidence before generating role-specific questions."),
            ("Evaluation flow", "Score answers and generate a structured review report."),
            ("Next integration", "Replace this deterministic executor with interview-agent."),
        ],
    )
    return TaskExecutionResult(
        executor="interview-executor",
        task_type=task_type,
        summary="Interview executor produced a deterministic prep outline.",
        markdown=markdown,
        output_format=_output_format(message),
    )


def file_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    markdown = _markdown_document(
        "File Analysis",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Storage flow", "Read file metadata and object keys from file-svc."),
            ("Parsing flow", "Use tool-registry parsers to extract reusable context."),
            ("Next integration", "Replace this deterministic executor with file-agent."),
        ],
    )
    return TaskExecutionResult(
        executor="file-executor",
        task_type=task_type,
        summary="File executor produced a deterministic parsing outline.",
        markdown=markdown,
        output_format=_output_format(message),
    )


def generic_executor(message: TaskMessage) -> TaskExecutionResult:
    task_type = _task_type(message)
    goal = _goal(message)
    markdown = _markdown_document(
        "Generic Task Result",
        [
            ("Task type", task_type),
            ("Goal", goal),
            ("Worker", "agent-worker consumed the RabbitMQ message."),
            (
                "Next integration",
                "Add a dedicated executor or route this task through planner-agent.",
            ),
        ],
    )
    return TaskExecutionResult(
        executor="generic-executor",
        task_type=task_type,
        summary="Generic executor completed the phase 1 deterministic task.",
        markdown=markdown,
        output_format=_output_format(message),
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


def _task_type(message: TaskMessage) -> str:
    return str(message.get("task_type") or "unknown")


def _goal(message: TaskMessage) -> str:
    return str(message.get("goal") or "")


def _output_format(message: TaskMessage) -> str:
    return str(message.get("output_format") or "Markdown")


def _markdown_document(title: str, rows: list[tuple[str, str]]) -> str:
    lines = [f"# {title}", ""]
    lines.extend(f"- {label}: {value}" for label, value in rows)
    return "\n".join(lines)
