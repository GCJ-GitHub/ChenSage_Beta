"""FastAPI dependencies for model-svc APIs."""

from __future__ import annotations

from fastapi import Request

from app.services.provider_store import ModelProviderStore


def get_provider_store(request: Request) -> ModelProviderStore:
    return request.app.state.provider_store
