"""Evaluation report behavior."""

from __future__ import annotations

from app.schemas.evaluation import EvaluationRequest
from app.services.evaluator import DeterministicEvaluator


def _request() -> EvaluationRequest:
    return EvaluationRequest(
        task_id="pytest-eval",
        task_type="content_generation",
        goal="写一篇公众号文章介绍阶段 7。",
        generated_content=(
            "# 公众号文章初稿\n\n"
            "## 开头\n阶段 7 开始提供内容评价。\n\n"
            "## 正文结构\n这里有结构。\n\n"
            "## 结尾\n继续改写。\n\n"
            "## Prompt Snapshot\nlocal debug"
        ),
        context={
            "content_task_spec": {
                "mode": "generation",
                "content_type": "公众号文章",
                "audience": "产品用户",
                "tone": "清晰",
                "length": "约 800 字",
            },
            "knowledge_context": {"item_count": 2},
        },
    )


def test_deterministic_evaluator_returns_structured_report() -> None:
    report = DeterministicEvaluator().evaluate(_request())

    assert report.type == "eval_report"
    assert report.overall_score >= 4
    assert report.scores["structure_integrity"] == 5
    assert report.score_reasons["factual_accuracy"].startswith("已引用 2 条知识来源")
    assert report.issue_locations[0].location == "结果尾部"
    assert report.revision_advice
    assert report.usable_highlights
    assert report.learning_candidates[0].status == "candidate"


def test_internal_evaluate_endpoint(client) -> None:
    response = client.post("/internal/evaluate", json=_request().model_dump())

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "eval_report"
    assert body["task_id"] == "pytest-eval"
    assert body["scores"]["platform_fit"] >= 4
    assert body["learning_candidates"]
