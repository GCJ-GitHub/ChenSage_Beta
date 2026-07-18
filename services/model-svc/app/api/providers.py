"""Model provider configuration APIs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_provider_store
from app.schemas.providers import (
    ModelProviderResponse,
    ModelProviderTestRequest,
    ModelProviderTestResponse,
    ModelProviderUpdateRequest,
)
from app.services.model_router import ModelRouter
from app.services.provider_store import ModelProviderStore

router = APIRouter(prefix="/model-providers", tags=["model-providers"])


@router.get("/default", response_model=ModelProviderResponse)
def get_default_provider(
    store: Annotated[ModelProviderStore, Depends(get_provider_store)],
) -> ModelProviderResponse:
    return store.to_response()


@router.put("/default", response_model=ModelProviderResponse)
def update_default_provider(
    request: ModelProviderUpdateRequest,
    store: Annotated[ModelProviderStore, Depends(get_provider_store)],
) -> ModelProviderResponse:
    return store.to_response(store.update_default(request))


@router.post("/default/test", response_model=ModelProviderTestResponse)
def test_default_provider(
    request: ModelProviderTestRequest,
    store: Annotated[ModelProviderStore, Depends(get_provider_store)],
) -> ModelProviderTestResponse:
    return ModelRouter(store).test_default(request.prompt)
