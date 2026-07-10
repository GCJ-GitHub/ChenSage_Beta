"""Configuration boundary for model-svc.

This module intentionally reads secrets from environment variables only.
YAML files may describe provider structure, but they must not contain real API keys.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelServiceSettings:
    provider_base_url: str
    provider_api_key: str
    default_model: str
    encryption_key: str
    request_timeout_seconds: int = 60
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "ModelServiceSettings":
        return cls(
            provider_base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"),
            provider_api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""),
            default_model=os.getenv("DEFAULT_MODEL", "gpt-4.1"),
            encryption_key=os.getenv("MODEL_CONFIG_ENCRYPTION_KEY", ""),
            request_timeout_seconds=int(os.getenv("MODEL_REQUEST_TIMEOUT_SECONDS", "60")),
            max_retries=int(os.getenv("MODEL_MAX_RETRIES", "2")),
        )

    def validate_for_runtime(self) -> None:
        missing = []
        if not self.provider_api_key:
            missing.append("OPENAI_COMPATIBLE_API_KEY")
        if not self.encryption_key:
            missing.append("MODEL_CONFIG_ENCRYPTION_KEY")
        if missing:
            names = ", ".join(missing)
            raise ValueError(f"Missing required model-svc environment variables: {names}")
