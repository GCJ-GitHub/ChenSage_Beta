"""Runtime model provider configuration store.

The first implementation is process-local and seeded from environment variables.
Persistent encrypted storage can replace this boundary without changing API callers.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from config.settings import ModelServiceSettings

from app.schemas.providers import ModelProviderResponse, ModelProviderUpdateRequest, ProviderType

DEFAULT_PROVIDER_ID = "default"


@dataclass(frozen=True, slots=True)
class ModelProviderConfig:
    id: str
    name: str
    provider_type: ProviderType
    base_url: str
    api_key: str
    default_model: str
    enabled: bool
    source: str
    updated_at: datetime
    request_timeout_seconds: int
    max_retries: int

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key)


class ModelProviderStore:
    def __init__(self, settings: ModelServiceSettings | None = None) -> None:
        self.settings = settings or ModelServiceSettings.from_env()
        self._default_provider = self._from_settings(self.settings)

    def get_default(self) -> ModelProviderConfig:
        return self._default_provider

    def update_default(self, request: ModelProviderUpdateRequest) -> ModelProviderConfig:
        current = self._default_provider
        next_api_key = (
            current.api_key if request.api_key is None else _normalize_key(request.api_key)
        )
        self._default_provider = replace(
            current,
            name=request.name.strip(),
            provider_type=request.provider_type,
            base_url=request.base_url.rstrip("/"),
            api_key=next_api_key,
            default_model=request.default_model.strip(),
            enabled=request.enabled,
            source="runtime",
            updated_at=_now(),
        )
        return self._default_provider

    def to_response(self, provider: ModelProviderConfig | None = None) -> ModelProviderResponse:
        provider = provider or self._default_provider
        return ModelProviderResponse(
            id=provider.id,
            name=provider.name,
            provider_type=provider.provider_type,
            base_url=provider.base_url,
            default_model=provider.default_model,
            api_key_configured=provider.api_key_configured,
            api_key_preview=_preview_key(provider.api_key),
            enabled=provider.enabled,
            source="runtime" if provider.source == "runtime" else "environment",
            updated_at=provider.updated_at.isoformat(),
        )

    def _from_settings(self, settings: ModelServiceSettings) -> ModelProviderConfig:
        provider_type = _provider_type(settings.provider_type)
        return ModelProviderConfig(
            id=DEFAULT_PROVIDER_ID,
            name="Default provider",
            provider_type=provider_type,
            base_url=settings.provider_base_url.rstrip("/"),
            api_key=_normalize_key(settings.provider_api_key),
            default_model=settings.default_model,
            enabled=True,
            source="environment",
            updated_at=_now(),
            request_timeout_seconds=settings.request_timeout_seconds,
            max_retries=settings.max_retries,
        )


def _provider_type(value: str) -> ProviderType:
    if value == "openai_compatible":
        return "openai_compatible"
    return "deterministic"


def _normalize_key(value: str) -> str:
    value = value.strip()
    if value in {"", "replace_me", "replace_me_with_real_key"}:
        return ""
    return value


def _preview_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:3]}...{value[-4:]}"


def _now() -> datetime:
    return datetime.now(tz=UTC).replace(microsecond=0)
