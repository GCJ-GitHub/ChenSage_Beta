"""Internal model generation API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_provider_store
from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse
from app.services.model_router import ModelRouter
from app.services.openai_compatible_provider import ModelProviderError
from app.services.provider_store import ModelProviderStore

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/generate", response_model=ModelGenerateResponse)
def generate(
    request: ModelGenerateRequest,
    store: Annotated[ModelProviderStore, Depends(get_provider_store)],
) -> ModelGenerateResponse:
    try:
        return ModelRouter(store).generate(request)
    except ModelProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
