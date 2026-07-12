"""Task executor registry behavior."""

from __future__ import annotations

import pytest
from app.executors import execute_task, get_executor


@pytest.mark.parametrize(
    ("task_type", "executor_name", "heading"),
    [
        ("content", "content-executor", "# Content Draft"),
        ("research", "research-executor", "# Research Brief"),
        ("arxiv", "arxiv-executor", "# arXiv Daily Brief"),
        ("interview", "interview-executor", "# Interview Prep"),
        ("file", "file-executor", "# File Analysis"),
    ],
)
def test_execute_task_uses_registered_executor(
    task_type: str,
    executor_name: str,
    heading: str,
) -> None:
    result = execute_task(
        {
            "task_type": task_type,
            "goal": "Validate executor routing.",
            "template": "pytest",
            "output_format": "Markdown",
        }
    )

    assert result.executor == executor_name
    assert result.task_type == task_type
    assert heading in result.markdown
    assert result.to_payload()["executor"] == executor_name


@pytest.mark.parametrize(
    "task_type",
    ["content_generation", "content_rewrite", "essay", "novel", "standup_script"],
)
def test_content_aliases_reuse_content_executor(task_type: str) -> None:
    result = execute_task({"task_type": task_type, "goal": "Write content."})

    assert result.executor == "content-executor"
    assert result.task_type == task_type
    assert "Content Draft" in result.markdown


def test_unknown_task_type_uses_generic_executor() -> None:
    result = execute_task({"task_type": "custom_future_task", "goal": "Handle safely."})

    assert result.executor == "generic-executor"
    assert result.task_type == "custom_future_task"
    assert "Generic Task Result" in result.markdown


def test_get_executor_returns_generic_fallback() -> None:
    assert get_executor("missing-task-type")({"goal": "Fallback."}).executor == "generic-executor"
