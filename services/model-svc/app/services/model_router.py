"""Select the active model provider for generation and connectivity tests."""

from __future__ import annotations

from time import perf_counter

from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse
from app.schemas.providers import ModelProviderTestResponse
from app.services.deterministic_provider import DeterministicModelProvider
from app.services.openai_compatible_provider import ModelProviderError, OpenAICompatibleProvider
from app.services.provider_store import ModelProviderStore


class ModelRouter:
    def __init__(self, provider_store: ModelProviderStore) -> None:
        self.provider_store = provider_store

    def generate(self, request: ModelGenerateRequest) -> ModelGenerateResponse:
        config = self.provider_store.get_default()
        if not config.enabled:
            raise ModelProviderError("Default model provider is disabled.")
        if config.provider_type == "openai_compatible":
            return OpenAICompatibleProvider(config).generate(request)
        return DeterministicModelProvider(default_model=config.default_model).generate(request)

    def test_default(self, prompt: str) -> ModelProviderTestResponse:
        config = self.provider_store.get_default()
        started_at = perf_counter()
        try:
            response = self.generate(
                ModelGenerateRequest(
                    task_id="model-provider-test",
                    agent="model-svc",
                    task_type="provider_test",
                    goal="Validate the active model provider.",
                    prompt=prompt,
                    output_format="Markdown",
                    metadata={"provider_id": config.id},
                )
            )
        except ModelProviderError as exc:
            return ModelProviderTestResponse(
                status="failed",
                provider_id=config.id,
                provider=config.provider_type,
                model=config.default_model,
                latency_ms=_elapsed_ms(started_at),
                message="Model provider connectivity test failed.",
                error=str(exc),
            )
        return ModelProviderTestResponse(
            status="succeeded",
            provider_id=config.id,
            provider=response.provider,
            model=response.model,
            latency_ms=_elapsed_ms(started_at),
            message="Model provider connectivity test succeeded.",
        )


def _elapsed_ms(started_at: float) -> int:
    return max(0, int((perf_counter() - started_at) * 1000))
