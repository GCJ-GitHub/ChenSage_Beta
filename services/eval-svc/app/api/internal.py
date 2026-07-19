"""Internal evaluation API."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.evaluation import EvaluationReport, EvaluationRequest
from app.services.evaluator import DeterministicEvaluator

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/evaluate", response_model=EvaluationReport)
def evaluate(request: EvaluationRequest) -> EvaluationReport:
    return DeterministicEvaluator().evaluate(request)
