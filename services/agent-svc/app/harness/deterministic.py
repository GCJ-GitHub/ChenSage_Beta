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
from app.services.eval_client import EvalClientProtocol, HttpEvalClient
from app.services.model_client import HttpModelClient, ModelClientProtocol
from app.services.prompt_builder import PromptBuilder

CONTENT_TASK_TYPES = {
    "content",
    "content_generation",
    "content_rewrite",
    "essay",
    "novel",
    "speech_script",
    "standup_script",
}


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    name: str
    role: str


class AgentHarness:
    def __init__(
        self,
        loop_engine: DeterministicLoopEngine | None = None,
        model_client: ModelClientProtocol | None = None,
        eval_client: EvalClientProtocol | None = None,
        prompt_builder: PromptBuilder | None = None,
        context_engine: KnowledgeContextEngine | None = None,
    ) -> None:
        self.loop_engine = loop_engine or DeterministicLoopEngine()
        self.model_client = model_client or HttpModelClient()
        self.eval_client = eval_client or HttpEvalClient()
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
        artifacts = []
        context_artifact = knowledge_context.to_artifact()
        if context_artifact:
            artifacts.append(context_artifact)
        eval_events: list[AgentExecutionStep] = []
        if request.task_type in CONTENT_TASK_TYPES and agent.name == "content-agent":
            eval_report, eval_event = self._evaluate_content(
                request=request,
                generated_content=str(model_response["markdown"]),
                artifacts=artifacts,
            )
            eval_events.append(eval_event)
            if eval_report:
                artifacts.append(eval_report)
        trace = [
            *loop.trace[:-1],
            context_event,
            *model_events,
            *eval_events,
            loop.trace[-1],
        ]
        duration_ms = sum(step.duration_ms for step in trace)
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

    def _evaluate_content(
        self,
        *,
        request: AgentExecutionRequest,
        generated_content: str,
        artifacts: list[dict[str, object]],
    ) -> tuple[dict[str, object] | None, AgentExecutionStep]:
        context = {
            "content_task_spec": _content_context_from_request(request),
            "knowledge_context": _artifact_by_type(artifacts, "knowledge_context"),
        }
        try:
            report = self.eval_client.evaluate(
                request=request,
                generated_content=generated_content,
                context=context,
            )
        except Exception as exc:
            return None, AgentExecutionStep(
                name="eval.unavailable",
                detail="eval-svc could not be reached; continuing without evaluation report.",
                phase="observe",
                status="failed",
                duration_ms=1,
                data={"error": str(exc)},
            )
        return report, AgentExecutionStep(
            name="eval.completed",
            detail="eval-svc returned a content evaluation report.",
            phase="observe",
            duration_ms=1,
            data={
                "overall_score": report.get("overall_score"),
                "learning_candidates": len(report.get("learning_candidates") or []),
            },
        )


def _artifact_by_type(
    artifacts: list[dict[str, object]],
    artifact_type: str,
) -> dict[str, object] | None:
    return next((artifact for artifact in artifacts if artifact.get("type") == artifact_type), None)


def _content_context_from_request(request: AgentExecutionRequest) -> dict[str, object]:
    task_input = request.input
    return {
        "mode": "rewrite"
        if request.task_type == "content_rewrite" or task_input.get("generated_content")
        else "generation",
        "content_type": task_input.get("content_type") or request.task_type,
        "audience": task_input.get("audience") or "未指定",
        "tone": task_input.get("tone") or "未指定",
        "length": task_input.get("length") or task_input.get("set_length") or "未指定",
    }
