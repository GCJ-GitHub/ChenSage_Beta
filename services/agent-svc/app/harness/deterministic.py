"""Shared deterministic agent harness."""

from __future__ import annotations

from dataclasses import dataclass

from app.context_engine import KnowledgeContextEngine
from app.loop_engine import DeterministicLoopEngine
from app.schemas.execution import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentExecutionResult,
    AgentExecutionStep,
)
from app.services.model_client import HttpModelClient, ModelClientProtocol
from app.services.prompt_builder import PromptBuilder


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    name: str
    role: str


class AgentHarness:
    def __init__(
        self,
        loop_engine: DeterministicLoopEngine | None = None,
        model_client: ModelClientProtocol | None = None,
        prompt_builder: PromptBuilder | None = None,
        context_engine: KnowledgeContextEngine | None = None,
    ) -> None:
        self.loop_engine = loop_engine or DeterministicLoopEngine()
        self.model_client = model_client or HttpModelClient()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.context_engine = context_engine or KnowledgeContextEngine()

    def run(
        self,
        *,
        request: AgentExecutionRequest,
        agent: AgentDefinition,
        executor: str,
        plan: list[AgentExecutionStep],
    ) -> AgentExecutionResponse:
        loop = self.loop_engine.run(agent_name=agent.name, request=request, plan=plan)
        knowledge_context = self.context_engine.retrieve(request)
        prompt = self.prompt_builder.build(
            request=request,
            agent=agent,
            executor=executor,
            plan=plan,
            knowledge_context=knowledge_context,
        )
        model_response = self.model_client.generate(
            request=request,
            agent=agent,
            prompt=prompt,
        )
        model_events = [
            AgentExecutionStep(
                name="model.requested",
                detail=f"Requested model generation from model-svc for {agent.name}.",
                phase="act",
                agent=agent.name,
                duration_ms=1,
                data={"provider": model_response.get("provider")},
            ),
            AgentExecutionStep(
                name="model.completed",
                detail=f"model-svc returned {model_response.get('model')}.",
                phase="observe",
                agent=agent.name,
                duration_ms=1,
                data={"usage": model_response.get("usage", {})},
            ),
        ]
        context_event = knowledge_context.to_trace_step()
        trace = [*loop.trace[:-1], context_event, *model_events, loop.trace[-1]]
        duration_ms = sum(step.duration_ms for step in trace)
        artifacts = []
        context_artifact = knowledge_context.to_artifact()
        if context_artifact:
            artifacts.append(context_artifact)
        result = AgentExecutionResult(
            format=request.output_format or "Markdown",
            markdown=str(model_response["markdown"]),
            summary=str(model_response["summary"]),
            executor=executor,
            task_type=request.task_type,
            steps=plan,
            trace=trace,
            duration_ms=duration_ms,
            provider=str(model_response.get("provider") or ""),
            model=str(model_response.get("model") or ""),
            usage=dict(model_response.get("usage") or {}),
            artifacts=artifacts,
        )
        return AgentExecutionResponse(
            task_id=request.task_id,
            task_type=request.task_type,
            executor=executor,
            result=result,
            events=trace,
            trace=trace,
        )
