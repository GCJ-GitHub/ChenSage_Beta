"""Prompt construction boundary before a formal prompt registry exists."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep

if TYPE_CHECKING:
    from app.harness import AgentDefinition


class PromptBuilder:
    def build(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        executor: str,
        plan: list[AgentExecutionStep],
    ) -> str:
        lines = [
            f"Agent: {agent.name}",
            f"Role: {agent.role}",
            f"Executor: {executor}",
            f"Task type: {request.task_type}",
            f"Goal: {request.goal}",
            f"Template: {request.template or 'default'}",
            f"Output format: {request.output_format or 'Markdown'}",
            "",
            "Plan:",
        ]
        lines.extend(f"{index}. {step.name}: {step.detail}" for index, step in enumerate(plan, 1))
        if request.input:
            lines.extend(["", f"Input keys: {', '.join(sorted(request.input.keys()))}"])
        return "\n".join(lines)
