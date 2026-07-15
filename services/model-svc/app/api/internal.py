"""Internal model generation API."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse
from app.services.deterministic_provider import DeterministicModelProvider

router = APIRouter(prefix="/internal", tags=["internal"])
provider = DeterministicModelProvider()


@router.post("/generate", response_model=ModelGenerateResponse)
def generate(request: ModelGenerateRequest) -> ModelGenerateResponse:
    return provider.generate(request)
