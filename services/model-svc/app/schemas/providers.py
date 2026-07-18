"""Schemas for model provider configuration APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProviderType = Literal["deterministic", "openai_compatible"]
ProviderTestStatus = Literal["succeeded", "failed"]


class ModelProviderUpdateRequest(BaseModel):
    name: str = Field(default="Default provider", min_length=1, max_length=120)
    provider_type: ProviderType = "deterministic"
    base_url: str = Field(default="https://api.openai.com/v1", min_length=1, max_length=500)
    default_model: str = Field(default="gpt-4.1", min_length=1, max_length=120)
    api_key: str | None = Field(default=None, max_length=4000)
    enabled: bool = True


class ModelProviderResponse(BaseModel):
    id: str
    name: str
    provider_type: ProviderType
    base_url: str
    default_model: str
    api_key_configured: bool
    api_key_preview: str
    enabled: bool
    source: Literal["environment", "runtime"]
    updated_at: str


class ModelProviderTestRequest(BaseModel):
    prompt: str = Field(
        default="Return a one-sentence connectivity confirmation.",
        min_length=1,
        max_length=2000,
    )


class ModelProviderTestResponse(BaseModel):
    status: ProviderTestStatus
    provider_id: str
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    message: str
    error: str | None = None
