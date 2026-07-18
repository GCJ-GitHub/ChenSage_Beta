"""Test fixtures for model-svc."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import create_app  # noqa: E402


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MODEL_PROVIDER_TYPE", "deterministic")
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    monkeypatch.setenv("DEFAULT_MODEL", "gpt-4.1")
    return TestClient(create_app())
