"""Shared deterministic agent harness."""

from __future__ import annotations

from dataclasses import dataclass

from app.loop_engine import DeterministicLoopEngine
from app.schemas.execution import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentExecutionResult,
    AgentExecutionStep,
)


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    name: str
    role: str


class AgentHarness:
    def __init__(self, loop_engine: DeterministicLoopEngine | None = None) -> None:
        self.loop_engine = loop_engine or DeterministicLoopEngine()

    def run(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        executor: str,
        summary: str,
        markdown: str,
        plan: list[AgentExecutionStep],
    ) -> AgentExecutionResponse:
        loop = self.loop_engine.run(agent_name=agent.name, request=request, plan=plan)
        result = AgentExecutionResult(
            format=request.output_format or "Markdown",
            markdown=markdown,
            summary=summary,
            executor=executor,
            task_type=request.task_type,
            steps=plan,
            trace=loop.trace,
            duration_ms=loop.duration_ms,
        )
        return AgentExecutionResponse(
            task_id=request.task_id,
            task_type=request.task_type,
            executor=executor,
            result=result,
            events=loop.trace,
            trace=loop.trace,
        )
