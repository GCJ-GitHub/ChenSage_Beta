"""Test fixtures for knowledge-base-svc."""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.db import session_scope  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.knowledge import KnowledgeItemModel  # noqa: E402

TEST_TITLE_PREFIX = "Pytest "


def clean_test_knowledge_items() -> None:
    with session_scope() as session:
        session.execute(
            delete(KnowledgeItemModel).where(
                KnowledgeItemModel.title.like(f"{TEST_TITLE_PREFIX}%")
            )
        )


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None]:
    clean_test_knowledge_items()
    yield
    clean_test_knowledge_items()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
