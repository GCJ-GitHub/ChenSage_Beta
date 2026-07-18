"""Deterministic conversation-agent for phase 5 task routing."""

from __future__ import annotations

from typing import Any

from app.context_engine import KnowledgeContextEngine
from app.schemas.conversation import (
    ConversationInterpretRequest,
    ConversationInterpretResponse,
    ConversationKnowledgeSource,
    ConversationTaskDraft,
    ConversationTemplateChoice,
)
from app.schemas.execution import AgentExecutionRequest
from app.services.prompt_registry import PromptRegistry

REWRITE_MARKERS = ("改写", "润色", "重写", "优化这段", "修改这段", "rewrite", "revise", "polish")
STANDUP_MARKERS = ("脱口秀", "单口", "standup", "stand-up")
XIAOHONGSHU_MARKERS = ("小红书", "种草")
ZHISHU_MARKERS = ("知乎",)
WECHAT_MARKERS = ("公众号", "微信")
LYRIC_MARKERS = ("歌词",)
SCRIPT_MARKERS = ("剧本", "短视频脚本", "脚本")
NOVEL_MARKERS = ("小说",)
PAPER_MARKERS = ("论文",)
PATENT_MARKERS = ("专利",)


class ConversationAgent:
    def __init__(
        self,
        *,
        registry: PromptRegistry,
        context_engine: KnowledgeContextEngine | None = None,
    ) -> None:
        self.registry = registry
        self.context_engine = context_engine or KnowledgeContextEngine()

    def interpret(self, request: ConversationInterpretRequest) -> ConversationInterpretResponse:
        message = request.message.strip()
        task_type = _infer_task_type(message)
        content_type = _infer_content_type(message, task_type)
        tone = _infer_tone(message, content_type)
        audience = _infer_audience(message)
        length = _infer_length(message)
        template = self.registry.resolve(
            template_id=_preferred_template(message),
            task_type=task_type,
        )
        task_input: dict[str, Any] = {
            "source": "conversation-workbench",
            "content_type": content_type,
            "audience": audience,
            "tone": tone,
            "length": length,
            "set_length": length,
            "topic": message,
            "conversation_message": message,
        }
        if task_type == "content_rewrite":
            task_input["generated_content"] = message
            task_input["rewrite_instruction"] = message

        draft = ConversationTaskDraft(
            task_type=task_type,
            goal=message,
            template=template.id,
            output_format=request.output_format or "Markdown",
            input=task_input,
        )
        knowledge_context = self.context_engine.retrieve(
            AgentExecutionRequest(
                task_id="conversation-preview",
                task_type=task_type,
                goal=message,
                input=task_input,
                template=template.id,
                output_format=draft.output_format,
            )
        )
        questions = _clarification_questions(message, task_type, audience)
        return ConversationInterpretResponse(
            reply=_build_reply(task_type, template.name, knowledge_context.item_count, questions),
            confidence=_confidence_for(message, task_type),
            selected_agent="content-agent",
            task=draft,
            template=ConversationTemplateChoice(
                id=template.id,
                name=template.name,
                version=template.version,
            ),
            knowledge_scope={
                "task_type": knowledge_context.task_type,
                "item_count": knowledge_context.item_count,
                "status": "unavailable" if knowledge_context.error else "ready",
                "error": knowledge_context.error,
            },
            knowledge_sources=[
                ConversationKnowledgeSource(
                    id=item.get("id"),
                    title=item.get("title"),
                    status=item.get("status"),
                    quality_score=item.get("quality_score"),
                    source_type=item.get("source_type"),
                    sources=item.get("sources", []),
                )
                for item in knowledge_context.items
            ],
            clarification_questions=questions,
        )


def _infer_task_type(message: str) -> str:
    lowered = message.casefold()
    if any(marker in lowered for marker in REWRITE_MARKERS):
        return "content_rewrite"
    return "content_generation"


def _preferred_template(message: str) -> str | None:
    lowered = message.casefold()
    if any(marker in lowered for marker in STANDUP_MARKERS):
        return "content.standup_script"
    return None


def _infer_content_type(message: str, task_type: str) -> str:
    lowered = message.casefold()
    if any(marker in lowered for marker in STANDUP_MARKERS):
        return "脱口秀 / 单口喜剧稿"
    if any(marker in lowered for marker in XIAOHONGSHU_MARKERS):
        return "小红书笔记"
    if any(marker in lowered for marker in ZHISHU_MARKERS):
        return "知乎回答"
    if any(marker in lowered for marker in WECHAT_MARKERS):
        return "公众号文章"
    if any(marker in lowered for marker in LYRIC_MARKERS):
        return "歌词"
    if any(marker in lowered for marker in SCRIPT_MARKERS):
        return "脚本"
    if any(marker in lowered for marker in NOVEL_MARKERS):
        return "小说"
    if any(marker in lowered for marker in PAPER_MARKERS):
        return "论文"
    if any(marker in lowered for marker in PATENT_MARKERS):
        return "专利"
    return "改写内容" if task_type == "content_rewrite" else "内容"


def _infer_tone(message: str, content_type: str) -> str:
    lowered = message.casefold()
    if "幽默" in lowered or "好笑" in lowered or "脱口秀" in content_type:
        return "幽默"
    if "专业" in lowered:
        return "专业"
    if "克制" in lowered:
        return "克制"
    if "清晰" in lowered:
        return "清晰"
    return "清晰"


def _infer_audience(message: str) -> str:
    if "开发者" in message:
        return "开发者"
    if "项目维护者" in message:
        return "项目维护者"
    if "HR" in message or "面试官" in message:
        return "招聘方"
    if "用户" in message:
        return "产品用户"
    return "未指定"


def _infer_length(message: str) -> str:
    for marker in ("分钟", "字", "段", "页"):
        index = message.find(marker)
        if index > 0:
            start = max(0, index - 8)
            return message[start : index + len(marker)].strip("，。；、 ")
    return "未指定"


def _clarification_questions(message: str, task_type: str, audience: str) -> list[str]:
    questions: list[str] = []
    if audience == "未指定":
        questions.append("目标读者是谁？")
    if task_type == "content_rewrite" and len(message) < 80:
        questions.append("需要改写的原文是否完整？")
    if "长度" not in message and "字" not in message and "分钟" not in message:
        questions.append("期望长度是多少？")
    return questions[:2]


def _confidence_for(message: str, task_type: str) -> float:
    if task_type == "content_rewrite":
        return 0.82
    if len(message) >= 20:
        return 0.86
    return 0.68


def _build_reply(
    task_type: str,
    template_name: str,
    knowledge_count: int,
    questions: list[str],
) -> str:
    action = "内容改写" if task_type == "content_rewrite" else "内容创作"
    knowledge_text = (
        f"已匹配 {knowledge_count} 条知识来源" if knowledge_count else "暂无匹配知识来源"
    )
    question_text = "，还有问题需要确认" if questions else ""
    return f"已整理为{action}任务，模板为「{template_name}」，{knowledge_text}{question_text}。"
