"""Internal execution API used by workers."""

from __future__ import annotations

from fastapi import APIRouter

from app.orchestrator.executors import execute_task
from app.schemas.execution import AgentExecutionRequest, AgentExecutionResponse

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/execute", response_model=AgentExecutionResponse)
def execute(request: AgentExecutionRequest) -> AgentExecutionResponse:
    return execute_task(request)
