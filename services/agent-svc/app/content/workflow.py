"""Content-agent workflow assembly for phase 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep

ContentMode = Literal["generation", "rewrite"]

CONTENT_REWRITE_TASK_TYPES = {"content_rewrite"}
STANDUP_CONTENT_TYPES = {"脱口秀 / 单口喜剧稿", "脱口秀稿", "单口喜剧稿", "standup_script"}


@dataclass(frozen=True, slots=True)
class ContentTaskSpec:
    mode: ContentMode
    content_type: str
    audience: str
    tone: str
    length: str
    topic: str
    rewrite_instruction: str
    generated_content: str

    @property
    def is_standup(self) -> bool:
        return self.content_type in STANDUP_CONTENT_TYPES


def build_content_task_spec(request: AgentExecutionRequest) -> ContentTaskSpec:
    task_input = request.input
    has_source_text = bool(_clean(task_input.get("generated_content")))
    is_rewrite = request.task_type in CONTENT_REWRITE_TASK_TYPES or has_source_text
    mode: ContentMode = "rewrite" if is_rewrite else "generation"
    content_type = _clean(task_input.get("content_type")) or _default_content_type(
        request.task_type
    )
    length = _clean(task_input.get("length")) or _clean(task_input.get("set_length")) or "未指定"
    generated_content = _clean(task_input.get("generated_content"))
    rewrite_instruction = _clean(task_input.get("rewrite_instruction")) or request.goal
    return ContentTaskSpec(
        mode=mode,
        content_type=content_type,
        audience=_clean(task_input.get("audience")) or "未指定",
        tone=_clean(task_input.get("tone")) or "清晰",
        length=length,
        topic=_clean(task_input.get("topic")) or request.goal,
        rewrite_instruction=rewrite_instruction,
        generated_content=generated_content,
    )


def build_content_plan(spec: ContentTaskSpec) -> list[AgentExecutionStep]:
    if spec.mode == "rewrite":
        return [
            AgentExecutionStep(
                name="content-agent.read_source",
                detail="Read source text and rewrite instruction.",
                data={"content_type": spec.content_type, "length": spec.length},
            ),
            AgentExecutionStep(
                name="content-agent.rewrite",
                detail="Rewrite while preserving core meaning and improving expression.",
                data={"audience": spec.audience, "tone": spec.tone},
            ),
            AgentExecutionStep(
                name="critic-agent.prepare_review",
                detail="Prepare a later pass for style consistency and omissions.",
            ),
        ]
    if spec.is_standup:
        return [
            AgentExecutionStep(
                name="content-agent.plan_set",
                detail="Plan hook, setup, turn, punchline, and callback.",
                data={"content_type": spec.content_type, "length": spec.length},
            ),
            AgentExecutionStep(
                name="content-agent.draft_script",
                detail="Draft a performable standup script with stage rhythm.",
                data={"audience": spec.audience, "tone": spec.tone},
            ),
            AgentExecutionStep(
                name="critic-agent.prepare_review",
                detail="Prepare safety and punchline density review.",
            ),
        ]
    return [
        AgentExecutionStep(
            name="content-agent.plan_outline",
            detail="Plan audience, angle, structure, and knowledge references.",
            data={"content_type": spec.content_type, "length": spec.length},
        ),
        AgentExecutionStep(
            name="content-agent.draft_content",
            detail="Generate a Markdown draft that follows the selected template.",
            data={"audience": spec.audience, "tone": spec.tone},
        ),
        AgentExecutionStep(
            name="critic-agent.prepare_review",
            detail="Prepare a later quality review for structure, style, and facts.",
        ),
    ]


def content_task_artifact(spec: ContentTaskSpec) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "type": "content_task_spec",
        "mode": spec.mode,
        "content_type": spec.content_type,
        "audience": spec.audience,
        "tone": spec.tone,
        "length": spec.length,
        "topic": spec.topic,
        "rewrite_instruction": spec.rewrite_instruction,
    }
    if spec.mode == "rewrite":
        artifact["source_text_preview"] = spec.generated_content[:240]
    return artifact


def _default_content_type(task_type: str) -> str:
    if task_type == "standup_script":
        return "脱口秀 / 单口喜剧稿"
    if task_type == "content_rewrite":
        return "改写内容"
    return "内容"


def _clean(value: Any) -> str:
    return str(value or "").strip()
