"""OpenAI-compatible chat completion provider boundary."""

from __future__ import annotations

from typing import Any

import httpx

from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse, ModelUsage
from app.services.provider_store import ModelProviderConfig


class ModelProviderError(RuntimeError):
    """Raised when a provider call fails without exposing secret material."""


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(
        self,
        config: ModelProviderConfig,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self.client = client or httpx.Client(trust_env=False)

    def generate(self, request: ModelGenerateRequest) -> ModelGenerateResponse:
        if not self.config.api_key:
            raise ModelProviderError("OpenAI-compatible provider API key is not configured.")
        payload = {
            "model": self.config.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are ChenSage model-svc. Return the requested content in the "
                        "requested output format without exposing provider secrets."
                    ),
                },
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.2,
        }
        try:
            response = self.client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise ModelProviderError(_sanitize_error(str(exc), self.config.api_key)) from exc
        except ValueError as exc:
            raise ModelProviderError("Provider returned invalid JSON.") from exc

        markdown = _extract_content(data)
        usage = _usage_from_response(data, request.prompt, markdown)
        return ModelGenerateResponse(
            provider=self.provider_name,
            model=str(data.get("model") or self.config.default_model),
            markdown=markdown,
            summary=_summary(markdown, request),
            usage=usage,
            trace={
                "task_id": request.task_id,
                "agent": request.agent,
                "task_type": request.task_type,
                "provider_id": self.config.id,
            },
        )


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ModelProviderError("Provider response did not include choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ModelProviderError("Provider response did not include message content.")
    return content


def _usage_from_response(
    data: dict[str, Any],
    prompt: str,
    markdown: str,
) -> ModelUsage:
    usage = data.get("usage")
    if isinstance(usage, dict):
        prompt_tokens = _positive_int(usage.get("prompt_tokens"))
        completion_tokens = _positive_int(usage.get("completion_tokens"))
        total_tokens = _positive_int(usage.get("total_tokens"))
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        return ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=max(1, total_tokens),
        )
    prompt_tokens = _estimate_tokens(prompt)
    completion_tokens = _estimate_tokens(markdown)
    return ModelUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )


def _positive_int(value: Any) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 0


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _summary(markdown: str, request: ModelGenerateRequest) -> str:
    first_line = next(
        (line.strip("# ").strip() for line in markdown.splitlines() if line.strip()),
        "",
    )
    if first_line:
        return first_line[:220]
    return f"{request.agent} generated {request.task_type} content."


def _sanitize_error(message: str, api_key: str) -> str:
    if api_key:
        message = message.replace(api_key, "[redacted]")
    return message[:1000]
