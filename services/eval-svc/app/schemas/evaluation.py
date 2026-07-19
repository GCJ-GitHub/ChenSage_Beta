"""Schemas for content evaluation reports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    task_id: str = Field(min_length=1, max_length=80)
    task_type: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=5000)
    generated_content: str = Field(min_length=1, max_length=20000)
    output_format: str | None = Field(default="Markdown", max_length=80)
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluationIssueLocation(BaseModel):
    location: str
    issue: str
    severity: Literal["low", "medium", "high"] = "medium"
    suggestion: str


class LearningCandidate(BaseModel):
    kind: Literal["style_preference", "structure_pattern", "quality_rule", "source_rule"]
    summary: str
    evidence: str
    confidence: float = Field(ge=0, le=1)
    status: Literal["candidate"] = "candidate"


class EvaluationReport(BaseModel):
    type: Literal["eval_report"] = "eval_report"
    task_id: str
    task_type: str
    overall_score: float = Field(ge=0, le=5)
    scores: dict[str, int]
    score_reasons: dict[str, str]
    issue_locations: list[EvaluationIssueLocation]
    revision_advice: list[str]
    usable_highlights: list[str]
    source_risks: list[str]
    learning_candidates: list[LearningCandidate]
    evaluator: str = "deterministic-eval-svc"
