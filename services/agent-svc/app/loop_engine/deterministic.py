"""Deterministic loop engine for the first agent-svc orchestration slice."""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep


@dataclass(frozen=True, slots=True)
class LoopRunResult:
    trace: list[AgentExecutionStep]
    duration_ms: int


class DeterministicLoopEngine:
    """Small plan -> act -> observe -> finalize loop without model calls."""

    def run(
        self,
        *,
        agent_name: str,
        request: AgentExecutionRequest,
        plan: list[AgentExecutionStep],
    ) -> LoopRunResult:
        trace: list[AgentExecutionStep] = [
            AgentExecutionStep(
                name=f"{agent_name}.plan",
                detail=f"Plan {len(plan)} deterministic steps for {request.task_type}.",
                phase="plan",
                agent=agent_name,
                duration_ms=1,
                data={"task_type": request.task_type},
            )
        ]

        for index, step in enumerate(plan, start=1):
            trace.append(
                step.model_copy(
                    update={
                        "phase": "act",
                        "agent": step.agent or agent_name,
                        "duration_ms": max(step.duration_ms, 1),
                        "data": {**step.data, "step_index": index},
                    }
                )
            )
            trace.append(
                AgentExecutionStep(
                    name=f"{step.name}.observe",
                    detail=f"Observed deterministic completion for {step.name}.",
                    phase="observe",
                    agent=step.agent or agent_name,
                    duration_ms=1,
                    data={"step_index": index, "source_step": step.name},
                )
            )

        trace.append(
            AgentExecutionStep(
                name=f"{agent_name}.finalize",
                detail="Finalize deterministic result payload for task-svc.",
                phase="finalize",
                agent=agent_name,
                duration_ms=1,
                data={"task_id": request.task_id},
            )
        )
        return LoopRunResult(
            trace=trace,
            duration_ms=sum(step.duration_ms for step in trace),
        )
