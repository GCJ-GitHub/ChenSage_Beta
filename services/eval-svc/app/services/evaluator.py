"""Deterministic content evaluator used by eval-svc."""

from __future__ import annotations

from statistics import mean
from typing import Any

from app.schemas.evaluation import (
    EvaluationIssueLocation,
    EvaluationReport,
    EvaluationRequest,
    LearningCandidate,
)

SCORE_KEYS = {
    "factual_accuracy": "事实准确性",
    "structure_integrity": "结构完整性",
    "style_match": "风格匹配度",
    "platform_fit": "平台适配度",
    "usability": "可直接使用度",
}


class DeterministicEvaluator:
    def evaluate(self, request: EvaluationRequest) -> EvaluationReport:
        content = request.generated_content
        context = request.context
        scores = _score_content(content=content, context=context)
        return EvaluationReport(
            task_id=request.task_id,
            task_type=request.task_type,
            overall_score=round(mean(scores.values()), 2),
            scores=scores,
            score_reasons=_score_reasons(scores, content, context),
            issue_locations=_issue_locations(content, context),
            revision_advice=_revision_advice(content, context),
            usable_highlights=_usable_highlights(content, context),
            source_risks=_source_risks(context),
            learning_candidates=_learning_candidates(request, content, context),
        )


def _score_content(*, content: str, context: dict[str, Any]) -> dict[str, int]:
    has_heading = content.lstrip().startswith("#")
    has_sections = content.count("\n## ") >= 2
    has_knowledge = _knowledge_item_count(context) > 0
    has_eval_markers = "## 主要调整" in content or "## 正文结构" in content
    return {
        "factual_accuracy": 4 if has_knowledge else 3,
        "structure_integrity": 5 if has_heading and has_sections else 3,
        "style_match": 4 if _content_spec(context).get("tone") not in {"", "未指定"} else 3,
        "platform_fit": 4 if _content_spec(context).get("content_type") else 3,
        "usability": 4 if has_eval_markers else 3,
    }


def _score_reasons(
    scores: dict[str, int],
    content: str,
    context: dict[str, Any],
) -> dict[str, str]:
    del content
    knowledge_count = _knowledge_item_count(context)
    spec = _content_spec(context)
    return {
        "factual_accuracy": (
            f"已引用 {knowledge_count} 条知识来源，事实风险较低。"
            if knowledge_count
            else "未发现可追溯知识来源，事实性只能做基础判断。"
        ),
        "structure_integrity": "内容包含 Markdown 标题和多个段落，结构可扫描。",
        "style_match": f"语气目标为「{spec.get('tone') or '未指定'}」，整体表达已按该方向组织。",
        "platform_fit": f"内容类型为「{spec.get('content_type') or '未指定'}」，已按平台草稿组织。",
        "usability": "已产出可继续修改的 Markdown 草稿，但仍建议补充具体案例或数据。",
    }


def _issue_locations(content: str, context: dict[str, Any]) -> list[EvaluationIssueLocation]:
    issues: list[EvaluationIssueLocation] = []
    if _knowledge_item_count(context) == 0:
        issues.append(
            EvaluationIssueLocation(
                location="知识来源",
                issue="本次输出没有关联知识库来源。",
                severity="medium",
                suggestion="补充资料来源或历史高质量案例后再生成一版。",
            )
        )
    if "Prompt Snapshot" in content:
        issues.append(
            EvaluationIssueLocation(
                location="结果尾部",
                issue="本地 deterministic 输出仍保留 Prompt Snapshot。",
                severity="low",
                suggestion="真实模型接入后隐藏调试快照，或导出前自动折叠。",
            )
        )
    if len(content) < 400:
        issues.append(
            EvaluationIssueLocation(
                location="全文",
                issue="内容篇幅偏短，论证和例子还不够。",
                severity="medium",
                suggestion="补充 1 到 2 个具体场景、数据或案例。",
            )
        )
    return issues[:3]


def _revision_advice(content: str, context: dict[str, Any]) -> list[str]:
    spec = _content_spec(context)
    advice = [
        "补充一个真实场景或示例，让观点更容易被验证。",
        "检查每个小节是否都服务于用户目标，删掉重复铺垫。",
    ]
    if spec.get("mode") == "rewrite":
        advice.insert(0, "对照原文逐段检查，确认核心事实和立场没有被改掉。")
    if "Prompt Snapshot" in content:
        advice.append("导出或正式展示前移除 Prompt Snapshot 调试内容。")
    return advice[:4]


def _usable_highlights(content: str, context: dict[str, Any]) -> list[str]:
    spec = _content_spec(context)
    highlights = [
        "输出为 Markdown，便于进入历史任务和后续导出。",
        "已保留任务目标、内容类型和语气等关键上下文。",
    ]
    if _knowledge_item_count(context):
        highlights.append("已带入知识库来源，后续可继续增强引用呈现。")
    if "## 主要调整" in content:
        highlights.append("改写稿列出了主要调整，便于人工复核。")
    if spec.get("content_type"):
        highlights.append(f"内容类型「{spec['content_type']}」已经进入评价上下文。")
    return highlights[:4]


def _source_risks(context: dict[str, Any]) -> list[str]:
    if _knowledge_item_count(context):
        return ["当前只校验知识来源存在，尚未做逐句事实核查。"]
    return ["缺少知识库来源，外部事实、引用和案例都需要人工复核。"]


def _learning_candidates(
    request: EvaluationRequest,
    content: str,
    context: dict[str, Any],
) -> list[LearningCandidate]:
    spec = _content_spec(context)
    candidates = [
        LearningCandidate(
            kind="structure_pattern",
            summary="内容草稿应保留 Markdown 标题、正文结构和结尾修改方向。",
            evidence="检测到 Markdown 输出和后续修改建议。",
            confidence=0.78,
        ),
        LearningCandidate(
            kind="quality_rule",
            summary="正式导出前应移除 Prompt Snapshot 调试区。",
            evidence="结果中包含 Prompt Snapshot。",
            confidence=0.86 if "Prompt Snapshot" in content else 0.62,
        ),
    ]
    if spec.get("tone") and spec.get("tone") != "未指定":
        candidates.append(
            LearningCandidate(
                kind="style_preference",
                summary=f"用户可能偏好「{spec['tone']}」语气的{spec.get('content_type', '内容')}。",
                evidence=request.goal,
                confidence=0.72,
            )
        )
    return candidates[:3]


def _content_spec(context: dict[str, Any]) -> dict[str, Any]:
    spec = context.get("content_task_spec")
    return spec if isinstance(spec, dict) else {}


def _knowledge_item_count(context: dict[str, Any]) -> int:
    knowledge = context.get("knowledge_context")
    if isinstance(knowledge, dict):
        return int(knowledge.get("item_count") or 0)
    return 0
