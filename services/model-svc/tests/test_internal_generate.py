"""Internal model generation API behavior."""

from __future__ import annotations

from app.schemas.generation import ModelGenerateRequest
from app.services.deterministic_provider import DeterministicModelProvider


def test_deterministic_provider_returns_markdown_and_usage() -> None:
    response = DeterministicModelProvider().generate(
        ModelGenerateRequest(
            task_id="pytest-model",
            agent="content-agent",
            task_type="content",
            goal="Write a deterministic draft.",
            prompt="Use a clear outline.",
            output_format="Markdown",
        )
    )

    assert response.provider == "deterministic"
    assert response.markdown.startswith("# content-agent Deterministic Output")
    assert response.usage.prompt_tokens > 0
    assert response.usage.total_tokens == (
        response.usage.prompt_tokens + response.usage.completion_tokens
    )


def test_internal_generate_endpoint(client) -> None:
    response = client.post(
        "/internal/generate",
        json={
            "task_id": "pytest-model-api",
            "agent": "research-agent",
            "task_type": "research_report",
            "goal": "Build a research plan.",
            "prompt": "Collect sources and summarize findings.",
            "output_format": "Markdown",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "deterministic"
    assert body["trace"]["agent"] == "research-agent"
    assert body["usage"]["total_tokens"] > 0
