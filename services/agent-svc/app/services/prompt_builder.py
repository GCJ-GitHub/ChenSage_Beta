"""Prompt construction boundary using the prompt template registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.context_engine import KnowledgeContext
from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep
from app.services.prompt_registry import PromptRegistry, build_template_values

if TYPE_CHECKING:
    from app.harness import AgentDefinition


class PromptBuilder:
    def __init__(self, registry: PromptRegistry | None = None) -> None:
        self.registry = registry or PromptRegistry()

    def build(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        executor: str,
        plan: list[AgentExecutionStep],
        knowledge_context: KnowledgeContext | None = None,
    ) -> str:
        template = self.registry.resolve(
            template_id=request.template,
            task_type=request.task_type,
        )
        rendered_template, missing_variables = self.registry.render(
            template=template,
            values=build_template_values(
                task_type=request.task_type,
                goal=request.goal,
                output_format=request.output_format,
                task_input=request.input,
            ),
        )
        lines = [
            f"Agent: {agent.name}",
            f"Role: {agent.role}",
            f"Executor: {executor}",
            f"Task type: {request.task_type}",
            f"Goal: {request.goal}",
            f"Template: {template.id}",
            f"Template name: {template.name}",
            f"Template version: {template.version}",
            f"Output format: {request.output_format or 'Markdown'}",
            "",
            "Rendered template:",
            rendered_template,
            "",
            "Plan:",
        ]
        lines.extend(f"{index}. {step.name}: {step.detail}" for index, step in enumerate(plan, 1))
        if request.input:
            lines.extend(["", f"Input keys: {', '.join(sorted(request.input.keys()))}"])
        if knowledge_context:
            prompt_section = knowledge_context.to_prompt_section()
            if prompt_section:
                lines.extend(["", prompt_section])
        if missing_variables:
            lines.extend(["", f"Missing template variables: {', '.join(missing_variables)}"])
        return "\n".join(lines)
