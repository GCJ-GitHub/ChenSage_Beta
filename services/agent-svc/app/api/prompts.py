"""Prompt template registry API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_prompt_registry
from app.schemas.prompts import PromptTemplateResponse
from app.services.prompt_registry import PromptRegistry, PromptTemplateNotFoundError

router = APIRouter(prefix="/prompt-templates", tags=["prompt-templates"])


@router.get("", response_model=list[PromptTemplateResponse])
def list_prompt_templates(
    registry: Annotated[PromptRegistry, Depends(get_prompt_registry)],
    task_type: Annotated[str | None, Query(max_length=80)] = None,
) -> list[PromptTemplateResponse]:
    return registry.list_templates(task_type=task_type)


@router.get("/{template_id}", response_model=PromptTemplateResponse)
def get_prompt_template(
    template_id: str,
    registry: Annotated[PromptRegistry, Depends(get_prompt_registry)],
) -> PromptTemplateResponse:
    try:
        return registry.get_template(template_id)
    except PromptTemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found",
        ) from exc
