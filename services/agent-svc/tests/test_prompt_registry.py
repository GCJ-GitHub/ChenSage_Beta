"""Prompt template registry behavior."""

from __future__ import annotations

from app.harness import AgentDefinition
from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep
from app.services.prompt_builder import PromptBuilder
from app.services.prompt_registry import PromptRegistry


def test_prompt_registry_loads_config_templates() -> None:
    registry = PromptRegistry()

    templates = registry.list_templates()

    assert {template.id for template in templates} >= {
        "content.default",
        "content.rewrite",
        "content.standup_script",
        "generic.default",
        "research.default",
        "interview.default",
        "arxiv.daily",
    }


def test_prompt_registry_filters_by_task_type_alias() -> None:
    registry = PromptRegistry()

    templates = registry.list_templates(task_type="content")

    assert [template.id for template in templates] == [
        "content.default",
        "content.rewrite",
        "content.standup_script",
    ]


def test_prompt_template_api(client) -> None:
    response = client.get("/prompt-templates?task_type=content")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == "content.default"
    assert body[0]["variables"]["topic"]["required"] is True

    detail = client.get("/prompt-templates/content.default")
    assert detail.status_code == 200
    assert detail.json()["name"] == "通用内容创作"


def test_prompt_builder_renders_selected_template() -> None:
    prompt = PromptBuilder().build(
        request=AgentExecutionRequest(
            task_id="pytest-prompt",
            task_type="content",
            goal="介绍 ChenSage 阶段 3",
            template="content.default",
            input={"content_type": "公众号文章", "audience": "开发者", "tone": "清晰"},
            output_format="Markdown",
        ),
        agent=AgentDefinition(
            name="content-agent",
            role="Draft content.",
        ),
        executor="content-executor",
        plan=[AgentExecutionStep(name="content-agent", detail="Render template.")],
    )

    assert "Template: content.default" in prompt
    assert "Template version: 0.1.0" in prompt
    assert "请围绕主题「介绍 ChenSage 阶段 3」创作一篇「公众号文章」" in prompt
    assert "目标读者：开发者" in prompt


def test_prompt_builder_renders_rewrite_template() -> None:
    prompt = PromptBuilder().build(
        request=AgentExecutionRequest(
            task_id="pytest-rewrite-prompt",
            task_type="content_rewrite",
            goal="把这段话改得更清晰",
            input={
                "content_type": "公众号文章",
                "generated_content": "原文表达比较松散，需要重写。",
                "rewrite_instruction": "保留原意，结构更清楚。",
                "audience": "产品用户",
                "tone": "专业",
                "length": "约 500 字",
            },
            output_format="Markdown",
        ),
        agent=AgentDefinition(
            name="content-agent",
            role="Rewrite content.",
        ),
        executor="content-executor",
        plan=[AgentExecutionStep(name="content-agent.rewrite", detail="Rewrite source.")],
    )

    assert "Template: content.rewrite" in prompt
    assert "请根据改写要求处理原文" in prompt
    assert "保留原意，结构更清楚" in prompt
    assert "原文表达比较松散" in prompt


def test_execute_task_includes_rendered_template_prompt() -> None:
    from app.orchestrator.executors import execute_task

    response = execute_task(
        AgentExecutionRequest(
            task_id="pytest-template-execute",
            task_type="content",
            goal="写一段阶段 3 说明",
            template="content.default",
            input={"content_type": "说明文", "audience": "内部团队", "tone": "稳重"},
            output_format="Markdown",
        )
    )

    assert "Template: content.default" in response.result.markdown
    assert "你是 ChenSage 的 content-agent" in response.result.markdown
    assert "目标读者：内部团队" in response.result.markdown
