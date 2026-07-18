"""Knowledge retrieval boundary for agent context assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas.execution import AgentExecutionRequest, AgentExecutionStep
from app.services.knowledge_client import HttpKnowledgeBaseClient, KnowledgeBaseClientProtocol

CONTENT_TASK_TYPES = {
    "content",
    "content_generation",
    "content_rewrite",
    "essay",
    "novel",
    "speech_script",
    "standup_script",
}
RESEARCH_TASK_TYPES = {"research", "research_report", "information_collection"}
ARXIV_TASK_TYPES = {"arxiv", "arxiv_daily"}
INTERVIEW_TASK_TYPES = {"interview", "mock_interview"}
FILE_TASK_TYPES = {"file", "file_analysis"}


@dataclass(frozen=True, slots=True)
class KnowledgeContext:
    task_type: str
    items: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_prompt_section(self) -> str:
        if not self.items:
            return ""

        lines = ["Knowledge context:"]
        for index, item in enumerate(self.items, 1):
            title = str(item.get("title") or "Untitled")
            status = str(item.get("status") or "unknown")
            quality_score = item.get("quality_score")
            quality = "unscored" if quality_score is None else f"{float(quality_score):.2f}"
            lines.append(f"{index}. {title} [{status}, quality={quality}]")
            summary = str(item.get("summary") or "").strip()
            if summary:
                lines.append(f"   Summary: {summary}")
            chunks = item.get("chunks") or []
            for chunk in chunks[:2]:
                text = str(chunk.get("text") or "").strip()
                if text:
                    lines.append(f"   Chunk: {text}")
            sources = item.get("sources") or []
            source_labels = [
                self._format_source(source)
                for source in sources[:3]
                if source.get("title") or source.get("uri")
            ]
            if source_labels:
                lines.append(f"   Sources: {'; '.join(source_labels)}")
        return "\n".join(lines)

    def to_artifact(self) -> dict[str, Any] | None:
        if not self.items:
            return None
        return {
            "type": "knowledge_context",
            "task_type": self.task_type,
            "item_count": self.item_count,
            "items": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "status": item.get("status"),
                    "quality_score": item.get("quality_score"),
                    "source_type": item.get("source_type"),
                    "sources": item.get("sources", []),
                }
                for item in self.items
            ],
        }

    def to_trace_step(self) -> AgentExecutionStep:
        if self.error:
            return AgentExecutionStep(
                name="context.knowledge_unavailable",
                detail=(
                    "knowledge-base-svc could not be reached; "
                    "continuing without retrieved context."
                ),
                phase="observe",
                status="failed",
                data={"task_type": self.task_type, "error": self.error},
            )
        return AgentExecutionStep(
            name="context.knowledge_retrieved",
            detail=f"Retrieved {self.item_count} knowledge item(s) for task type {self.task_type}.",
            phase="observe",
            data={
                "task_type": self.task_type,
                "item_count": self.item_count,
                "item_ids": [item.get("id") for item in self.items],
            },
        )

    @staticmethod
    def _format_source(source: dict[str, Any]) -> str:
        title = str(source.get("title") or source.get("source_type") or "source")
        uri = source.get("uri")
        return f"{title} ({uri})" if uri else title


class KnowledgeContextEngine:
    def __init__(
        self,
        client: KnowledgeBaseClientProtocol | None = None,
        *,
        max_items: int = 3,
    ) -> None:
        self.client = client or HttpKnowledgeBaseClient()
        self.max_items = max_items

    def retrieve(self, request: AgentExecutionRequest) -> KnowledgeContext:
        task_type = normalize_knowledge_task_type(request.task_type)
        try:
            items = self.client.search(
                task_type=task_type,
                status="active",
                tags=_knowledge_tags(request.input),
                limit=self.max_items,
            )
        except Exception as exc:
            return KnowledgeContext(task_type=task_type, error=str(exc))
        return KnowledgeContext(task_type=task_type, items=items)


def normalize_knowledge_task_type(task_type: str) -> str:
    if task_type in CONTENT_TASK_TYPES:
        return "content"
    if task_type in RESEARCH_TASK_TYPES:
        return "research"
    if task_type in ARXIV_TASK_TYPES:
        return "arxiv"
    if task_type in INTERVIEW_TASK_TYPES:
        return "interview"
    if task_type in FILE_TASK_TYPES:
        return "file"
    return task_type


def _knowledge_tags(task_input: dict[str, Any]) -> list[str]:
    tags = task_input.get("knowledge_tags")
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags if str(tag).strip()]
