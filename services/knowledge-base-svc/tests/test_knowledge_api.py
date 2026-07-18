"""Knowledge-base API behavior."""

from __future__ import annotations

from app.services.knowledge_store import KnowledgeStore


def _create_item(client, *, title: str = "Pytest high quality content example") -> dict:
    response = client.post(
        "/knowledge-items",
        json={
            "title": title,
            "summary": "Reusable writing pattern confirmed by user feedback.",
            "task_type": "content",
            "source_type": "generated_content",
            "status": "active",
            "quality_score": 0.88,
            "tags": ["Content", "Stage4", "Style"],
            "metadata": {"owner": "local"},
            "sources": [
                {
                    "source_type": "task_result",
                    "title": "Task result",
                    "uri": "task://pytest-knowledge",
                    "summary": "A completed content task.",
                }
            ],
            "chunks": [
                {
                    "text": "ChenSage knowledge retrieval should keep sources and quality signals.",
                    "ordinal": 0,
                    "source_refs": ["task://pytest-knowledge"],
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_item_with_chunks_and_sources(client) -> None:
    item = _create_item(client)

    assert item["id"]
    assert item["status"] == "active"
    assert item["tags"] == ["content", "stage4", "style"]
    assert item["sources"][0]["source_type"] == "task_result"
    assert item["chunks"][0]["token_count"] > 0
    assert item["embedding"] is None


def test_list_items_filters_by_task_type_status_tag_and_quality(client) -> None:
    _create_item(client)
    client.post(
        "/knowledge-items",
        json={
            "title": "Pytest draft research note",
            "task_type": "research",
            "source_type": "manual",
            "status": "draft",
            "quality_score": 0.2,
            "tags": ["stage4"],
        },
    )

    response = client.get(
        "/knowledge-items?task_type=content&status=active&tag=stage4&min_quality_score=0.8",
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["task_type"] == "content"


def test_search_items_matches_chunk_text(client) -> None:
    item = _create_item(client)

    response = client.post(
        "/knowledge-items/search",
        json={"task_type": "content", "tags": ["stage4"], "query": "quality signals"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == item["id"]


def test_item_persists_across_store_instances(client) -> None:
    item = _create_item(client, title="Pytest persistent content example")

    loaded = KnowledgeStore().get_item(item["id"])

    assert loaded.title == "Pytest persistent content example"
    assert loaded.sources[0].uri == "task://pytest-knowledge"


def test_add_source_and_chunk_to_existing_item(client) -> None:
    item = _create_item(client)

    source = client.post(
        f"/knowledge-items/{item['id']}/sources",
        json={
            "source_type": "url",
            "title": "Reference article",
            "uri": "https://example.test/reference",
            "summary": "External context.",
        },
    )
    chunk = client.post(
        f"/knowledge-items/{item['id']}/chunks",
        json={
            "text": "A later imported reference chunk.",
            "ordinal": 1,
            "source_refs": ["https://example.test/reference"],
        },
    )

    assert source.status_code == 201
    assert chunk.status_code == 201

    detail = client.get(f"/knowledge-items/{item['id']}")
    assert len(detail.json()["sources"]) == 2
    assert len(detail.json()["chunks"]) == 2


def test_missing_item_returns_404(client) -> None:
    response = client.get("/knowledge-items/missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"
