"""Validate the phase 0 repository skeleton.

This script intentionally checks structure and examples only. It does not require
Docker containers or real API keys to be running.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


REQUIRED_PATHS = [
    "apps/web/index.html",
    "apps/web/styles.css",
    "apps/web/app.js",
    "services/gateway/app/main.py",
    "services/task-svc/app/main.py",
    "services/model-svc/app/main.py",
    "services/agent-svc/app/main.py",
    "workers/agent-worker/app/main.py",
    "packages/shared/__init__.py",
    "infra/docker/docker-compose.yml",
    "infra/docker/.env.example",
    ".env.example",
    "config/app/development.yaml",
    "config/app/test.yaml",
    "config/app/production.example.yaml",
    "config/models/providers.example.yaml",
    "config/prompts/README.md",
]

REQUIRED_COMPOSE_SERVICES = [
    "postgres:",
    "rabbitmq:",
    "redis:",
    "minio:",
    "minio-init:",
]

FORBIDDEN_SECRET_VALUES = [
    "sk-",
    "ghp_",
    "xoxb-",
]


def fail(message: str) -> None:
    print(f"[fail] {message}")


def ok(message: str) -> None:
    print(f"[ ok ] {message}")


def check_paths() -> list[str]:
    errors: list[str] = []
    for relative_path in REQUIRED_PATHS:
        path = ROOT / relative_path
        if not path.exists():
            errors.append(f"Missing required path: {relative_path}")
    if not errors:
        ok("required directories and files exist")
    return errors


def check_compose() -> list[str]:
    errors: list[str] = []
    compose_file = ROOT / "infra/docker/docker-compose.yml"
    content = compose_file.read_text(encoding="utf-8")
    for service_name in REQUIRED_COMPOSE_SERVICES:
        if service_name not in content:
            errors.append(f"docker-compose.yml missing service: {service_name.rstrip(':')}")
    if not errors:
        ok("docker compose dependency services are declared")
    return errors


def check_env_examples() -> list[str]:
    errors: list[str] = []
    for relative_path in [".env.example", "infra/docker/.env.example"]:
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        for secret_marker in FORBIDDEN_SECRET_VALUES:
            if secret_marker in content:
                errors.append(
                    f"{relative_path} appears to contain a real secret marker: {secret_marker}"
                )
    if not errors:
        ok("env examples do not contain obvious real secret markers")
    return errors


def main() -> int:
    errors = []
    errors.extend(check_paths())
    errors.extend(check_compose())
    errors.extend(check_env_examples())

    if errors:
        for error in errors:
            fail(error)
        return 1

    ok("phase 0 skeleton is ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
