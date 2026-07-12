"""Test fixtures for task-svc."""

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
from app.models.tasks import TaskModel  # noqa: E402

TEST_TASK_TYPE_PREFIX = "pytest_"


def clean_test_tasks() -> None:
    with session_scope() as session:
        session.execute(
            delete(TaskModel).where(TaskModel.task_type.like(f"{TEST_TASK_TYPE_PREFIX}%"))
        )


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None]:
    clean_test_tasks()
    yield
    clean_test_tasks()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
