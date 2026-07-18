"""Deterministic provider used before real model credentials are wired."""

from __future__ import annotations

from config.settings import ModelServiceSettings

from app.schemas.generation import ModelGenerateRequest, ModelGenerateResponse, ModelUsage

CONTENT_TASK_TYPES = {
    "content",
    "content_generation",
    "content_rewrite",
    "essay",
    "novel",
    "speech_script",
    "standup_script",
}


class DeterministicModelProvider:
    provider_name = "deterministic"

    def __init__(
        self,
        settings: ModelServiceSettings | None = None,
        default_model: str | None = None,
    ) -> None:
        self.settings = settings or ModelServiceSettings.from_env()
        self.default_model = default_model

    def generate(self, request: ModelGenerateRequest) -> ModelGenerateResponse:
        model = self.default_model or self.settings.default_model or "deterministic-agentos"
        markdown = (
            _content_markdown(request)
            if request.agent == "content-agent" and request.task_type in CONTENT_TASK_TYPES
            else _generic_markdown(request)
        )
        prompt_tokens = _estimate_tokens(request.prompt)
        completion_tokens = _estimate_tokens(markdown)
        usage = ModelUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return ModelGenerateResponse(
            provider=self.provider_name,
            model=model,
            markdown=markdown,
            summary=_summary(request),
            usage=usage,
            trace={
                "task_id": request.task_id,
                "agent": request.agent,
                "task_type": request.task_type,
            },
        )


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _generic_markdown(request: ModelGenerateRequest) -> str:
    return "\n".join(
        [
            f"# {request.agent} Deterministic Output",
            "",
            f"- Task type: {request.task_type}",
            f"- Goal: {request.goal}",
            f"- Output format: {request.output_format or 'Markdown'}",
            "- Provider: deterministic model-svc boundary.",
            "",
            "## Prompt Snapshot",
            _compact_prompt(request.prompt),
        ]
    )


def _content_markdown(request: ModelGenerateRequest) -> str:
    task_input = _task_input(request)
    content_type = _value(task_input, "content_type", "内容")
    audience = _value(task_input, "audience", "未指定")
    tone = _value(task_input, "tone", "清晰")
    length = _value(task_input, "length", _value(task_input, "set_length", "未指定"))
    if request.task_type == "content_rewrite" or _value(task_input, "generated_content", ""):
        return _rewrite_markdown(request, content_type, audience, tone, length, task_input)
    if content_type in {"脱口秀 / 单口喜剧稿", "脱口秀稿", "单口喜剧稿"}:
        return _standup_markdown(request, audience, tone, length)
    return _draft_markdown(request, content_type, audience, tone, length)


def _draft_markdown(
    request: ModelGenerateRequest,
    content_type: str,
    audience: str,
    tone: str,
    length: str,
) -> str:
    return "\n".join(
        [
            f"# {content_type}初稿",
            "",
            f"> 目标：{request.goal}",
            f"> 读者：{audience} / 语气：{tone} / 长度：{length}",
            "",
            "## 开头",
            f"围绕「{request.goal}」，先用一个清晰问题把读者带入。",
            "",
            "## 正文结构",
            "1. 说明背景和真实痛点。",
            "2. 给出核心观点，并结合可用知识来源展开。",
            "3. 用一个具体场景说明方案如何落地。",
            "",
            "## 结尾",
            "收束到一个可继续改写的方向，并提示下一步可以补充案例或数据。",
            "",
            "## Prompt Snapshot",
            _compact_prompt(request.prompt),
        ]
    )


def _rewrite_markdown(
    request: ModelGenerateRequest,
    content_type: str,
    audience: str,
    tone: str,
    length: str,
    task_input: dict[str, object],
) -> str:
    instruction = _value(task_input, "rewrite_instruction", request.goal)
    source = _value(task_input, "generated_content", request.goal)
    return "\n".join(
        [
            f"# {content_type}改写稿",
            "",
            f"> 改写要求：{instruction}",
            f"> 读者：{audience} / 语气：{tone} / 长度：{length}",
            "",
            "## 改写稿",
            f"{source[:220]}",
            "",
            "这版会保留原意，压缩重复表达，并把结构改成更适合 Markdown 阅读的层次。",
            "",
            "## 主要调整",
            "- 明确读者和语气。",
            "- 保留核心观点，重排表达顺序。",
            "- 给后续人工细修留下可操作方向。",
            "",
            "## Prompt Snapshot",
            _compact_prompt(request.prompt),
        ]
    )


def _standup_markdown(
    request: ModelGenerateRequest,
    audience: str,
    tone: str,
    length: str,
) -> str:
    return "\n".join(
        [
            "# 脱口秀 / 单口喜剧稿初稿",
            "",
            f"> 主题：{request.goal}",
            f"> 观众：{audience} / 喜剧气质：{tone} / 时长：{length}",
            "",
            "## 开场 Hook",
            "我第一次用 AgentOS 的时候，感觉自己不是在打开软件，是在给人生新建任务队列。",
            "",
            "## 段落 1",
            "以前我管理任务靠记忆力，现在靠系统。区别是：系统至少会承认它忘了。",
            "",
            "## 段落 2",
            "它会把目标、模板和知识库串起来，听起来很高级，本质上就是终于有人替我把脑子里的标签贴正了。",
            "",
            "## Callback",
            "所以我现在不怕任务多，我怕的是任务突然问我：你这个需求验收标准是什么？",
            "",
            "## Prompt Snapshot",
            _compact_prompt(request.prompt),
        ]
    )


def _summary(request: ModelGenerateRequest) -> str:
    if request.agent == "content-agent" and request.task_type in CONTENT_TASK_TYPES:
        return f"content-agent generated deterministic {request.task_type} draft."
    return f"{request.agent} generated deterministic {request.task_type} content."


def _task_input(request: ModelGenerateRequest) -> dict[str, object]:
    task_input = request.metadata.get("input")
    return task_input if isinstance(task_input, dict) else {}


def _value(values: dict[str, object], key: str, default: str) -> str:
    value = values.get(key)
    text = str(value or "").strip()
    return text or default


def _compact_prompt(prompt: str) -> str:
    prompt = " ".join(prompt.split())
    if len(prompt) <= 1200:
        return prompt
    return f"{prompt[:1197]}..."
