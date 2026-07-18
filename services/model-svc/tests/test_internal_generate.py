"""Internal model generation API behavior."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
from app.schemas.generation import ModelGenerateRequest
from app.services.deterministic_provider import DeterministicModelProvider
from app.services.openai_compatible_provider import OpenAICompatibleProvider
from app.services.provider_store import ModelProviderConfig


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
    assert response.markdown.startswith("# 内容初稿")
    assert "Prompt Snapshot" in response.markdown
    assert response.usage.prompt_tokens > 0
    assert response.usage.total_tokens == (
        response.usage.prompt_tokens + response.usage.completion_tokens
    )


def test_deterministic_provider_returns_content_draft() -> None:
    response = DeterministicModelProvider().generate(
        ModelGenerateRequest(
            task_id="pytest-content-draft",
            agent="content-agent",
            task_type="content_generation",
            goal="介绍阶段 6 内容创作能力。",
            prompt="Rendered content prompt.",
            output_format="Markdown",
            metadata={
                "input": {
                    "content_type": "公众号文章",
                    "audience": "产品用户",
                    "tone": "清晰",
                    "length": "约 800 字",
                }
            },
        )
    )

    assert response.markdown.startswith("# 公众号文章初稿")
    assert "读者：产品用户 / 语气：清晰 / 长度：约 800 字" in response.markdown
    assert response.summary == "content-agent generated deterministic content_generation draft."


def test_deterministic_provider_returns_rewrite_draft() -> None:
    response = DeterministicModelProvider().generate(
        ModelGenerateRequest(
            task_id="pytest-content-rewrite",
            agent="content-agent",
            task_type="content_rewrite",
            goal="改写这段内容。",
            prompt="Rendered rewrite prompt.",
            output_format="Markdown",
            metadata={
                "input": {
                    "content_type": "公众号文章",
                    "generated_content": "原文需要更清晰的结构。",
                    "rewrite_instruction": "保留原意，表达更专业。",
                    "audience": "内部团队",
                    "tone": "专业",
                }
            },
        )
    )

    assert response.markdown.startswith("# 公众号文章改写稿")
    assert "改写要求：保留原意，表达更专业。" in response.markdown
    assert "原文需要更清晰的结构。" in response.markdown


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


def test_default_provider_endpoint_returns_masked_configuration(client) -> None:
    response = client.get("/model-providers/default")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "default"
    assert body["provider_type"] == "deterministic"
    assert body["api_key_configured"] is False
    assert body["api_key_preview"] == ""


def test_update_provider_masks_api_key_and_preserves_generation(client) -> None:
    update = client.put(
        "/model-providers/default",
        json={
            "name": "Local deterministic",
            "provider_type": "deterministic",
            "base_url": "https://example.test/v1",
            "default_model": "local-model",
            "api_key": "sk-test-secret-value",
            "enabled": True,
        },
    )

    assert update.status_code == 200
    body = update.json()
    assert body["api_key_configured"] is True
    assert body["api_key_preview"] == "sk-...alue"
    assert "secret-value" not in update.text

    generated = client.post(
        "/internal/generate",
        json={
            "task_id": "pytest-runtime-provider",
            "agent": "content-agent",
            "task_type": "content",
            "goal": "Use runtime config.",
            "prompt": "Return deterministic content.",
            "output_format": "Markdown",
        },
    )
    assert generated.status_code == 200
    assert generated.json()["model"] == "local-model"


def test_provider_connectivity_test_uses_deterministic_provider(client) -> None:
    response = client.post(
        "/model-providers/default/test",
        json={"prompt": "Validate deterministic provider."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["provider"] == "deterministic"


def test_openai_compatible_provider_without_key_fails_safely(client) -> None:
    client.put(
        "/model-providers/default",
        json={
            "name": "Missing key provider",
            "provider_type": "openai_compatible",
            "base_url": "https://example.test/v1",
            "default_model": "demo-model",
            "api_key": "",
            "enabled": True,
        },
    )

    response = client.post("/model-providers/default/test", json={"prompt": "Ping."})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "API key" in body["error"]


def test_openai_compatible_provider_parses_chat_completion_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://example.test/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer sk-test-secret"
        return httpx.Response(
            200,
            json={
                "model": "demo-model",
                "choices": [{"message": {"content": "# Mocked\n\nProvider result."}}],
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 5,
                    "total_tokens": 12,
                },
            },
        )

    provider = OpenAICompatibleProvider(
        ModelProviderConfig(
            id="default",
            name="Mock provider",
            provider_type="openai_compatible",
            base_url="https://example.test/v1",
            api_key="sk-test-secret",
            default_model="demo-model",
            enabled=True,
            source="runtime",
            updated_at=datetime.now(tz=UTC),
            request_timeout_seconds=10,
            max_retries=0,
        ),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = provider.generate(
        ModelGenerateRequest(
            task_id="pytest-openai-compatible",
            agent="content-agent",
            task_type="content",
            goal="Parse provider response.",
            prompt="Return markdown.",
            output_format="Markdown",
        )
    )

    assert response.provider == "openai_compatible"
    assert response.markdown.startswith("# Mocked")
    assert response.usage.total_tokens == 12
