"""Deterministic provider used before real model credentials are wired."""

from __future__ import annotations

from config.settings import ModelServiceSettings

from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse, ModelUsage


class DeterministicModelProvider:
    provider_name = "deterministic"

    def __init__(
        self,
        settings: ModelServiceSettings | None = None,
        default_model: str | None = None,
    ) -> None:
        self.settings = settings or ModelServiceSettings.from_env()
        self.default_model = default_model

    def generate(self, request: ModelGenerateRequest) -> ModelGenerateResponse:
        model = self.default_model or self.settings.default_model or "deterministic-agentos"
        markdown = "\n".join(
            [
                f"# {request.agent} Deterministic Output",
                "",
                f"- Task type: {request.task_type}",
                f"- Goal: {request.goal}",
                f"- Output format: {request.output_format or 'Markdown'}",
                "- Provider: deterministic model-svc boundary.",
                "",
                "## Prompt Snapshot",
                _compact_prompt(request.prompt),
            ]
        )
        prompt_tokens = _estimate_tokens(request.prompt)
        completion_tokens = _estimate_tokens(markdown)
        usage = ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return ModelGenerateResponse(
            provider=self.provider_name,
            model=model,
            markdown=markdown,
            summary=f"{request.agent} generated deterministic {request.task_type} content.",
            usage=usage,
            trace={
                "task_id": request.task_id,
                "agent": request.agent,
                "task_type": request.task_type,
            },
        )


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _compact_prompt(prompt: str) -> str:
    prompt = " ".join(prompt.split())
    if len(prompt) <= 420:
        return prompt
    return f"{prompt[:417]}..."
