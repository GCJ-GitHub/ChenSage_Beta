"""Conversation-agent task interpretation behavior."""

from __future__ import annotations

from app.context_engine import KnowledgeContext
from app.conversation import ConversationAgent
from app.schemas.conversation import ConversationInterpretRequest
from app.schemas.execution import AgentExecutionRequest
from app.services.prompt_registry import PromptRegistry


class FakeConversationContextEngine:
    def retrieve(self, request: AgentExecutionRequest) -> KnowledgeContext:
        return KnowledgeContext(
            task_type="content",
            items=[
                {
                    "id": "conversation-knowledge",
                    "title": f"{request.task_type} reusable source",
                    "summary": "A source selected for conversation task drafting.",
                    "status": "active",
                    "quality_score": 0.9,
                    "source_type": "generated_content",
                    "sources": [{"title": "Conversation source", "uri": "task://conversation"}],
                    "chunks": [{"text": "Keep the output structured and source-aware."}],
                }
            ],
        )


def _agent() -> ConversationAgent:
    return ConversationAgent(
        registry=PromptRegistry(),
        context_engine=FakeConversationContextEngine(),
    )


def test_conversation_agent_identifies_content_generation() -> None:
    response = _agent().interpret(
        ConversationInterpretRequest(
            message="写一篇公众号文章，主题是 AgentOS 的知识库能力，语气清晰。",
        )
    )

    assert response.task.task_type == "content_generation"
    assert response.task.template == "content.default"
    assert response.task.input["content_type"] == "公众号文章"
    assert response.task.input["length"] == "未指定"
    assert response.template.name == "通用内容创作"
    assert response.knowledge_sources[0].id == "conversation-knowledge"


def test_conversation_agent_identifies_content_rewrite() -> None:
    response = _agent().interpret(
        ConversationInterpretRequest(
            message="帮我改写这段公众号开头，让它更清晰专业。",
        )
    )

    assert response.task.task_type == "content_rewrite"
    assert response.task.template == "content.rewrite"
    assert response.task.input["generated_content"].startswith("帮我改写")
    assert response.task.input["rewrite_instruction"].startswith("帮我改写")
    assert response.confidence >= 0.8


def test_conversation_agent_prefers_standup_template() -> None:
    response = _agent().interpret(
        ConversationInterpretRequest(
            message="写一个 3 分钟脱口秀稿，主题是程序员第一次用 AgentOS。",
        )
    )

    assert response.task.task_type == "content_generation"
    assert response.task.template == "content.standup_script"
    assert response.task.input["content_type"] == "脱口秀 / 单口喜剧稿"
    assert "3 分钟" in response.task.input["length"]


def test_conversation_interpret_api(client) -> None:
    client.app.state.conversation_agent = _agent()
    response = client.post(
        "/conversation/interpret",
        json={"message": "写一篇知乎回答，解释个人知识库为什么重要。"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task"]["task_type"] == "content_generation"
    assert body["selected_agent"] == "content-agent"
    assert body["knowledge_scope"]["item_count"] == 1
    assert body["knowledge_sources"][0]["title"] == "content_generation reusable source"
