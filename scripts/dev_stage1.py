"""Run the phase 1-4 local development stack."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_step(command: Sequence[str], *, env: dict[str, str] | None = None) -> None:
    printable = " ".join(command)
    print(f"\n$ {printable}", flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def start_process(
    name: str,
    command: Sequence[str],
    *,
    env: dict[str, str],
) -> subprocess.Popen:
    printable = " ".join(command)
    print(f"\n[{name}] starting: {printable}", flush=True)
    return subprocess.Popen(command, cwd=ROOT, env=env)


def stop_processes(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the ChenSage phase 1-4 local stack.")
    parser.add_argument("--skip-infra", action="store_true", help="Do not start Docker Compose.")
    parser.add_argument(
        "--skip-migrate",
        action="store_true",
        help="Do not run Alembic migrations.",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("TASK_SVC_URL", "http://127.0.0.1:8011")
    env.setdefault("MODEL_SVC_URL", "http://127.0.0.1:8012")
    env.setdefault("AGENT_SVC_URL", "http://127.0.0.1:8013")
    env.setdefault("KNOWLEDGE_BASE_SVC_URL", "http://127.0.0.1:8014")
    env.setdefault("PYTHONUNBUFFERED", "1")

    if not args.skip_infra:
        run_step(
            [
                "docker",
                "compose",
                "--env-file",
                "infra/docker/.env",
                "-f",
                "infra/docker/docker-compose.yml",
                "up",
                "-d",
            ],
            env=env,
        )

    if not args.skip_migrate:
        run_step(
            [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                "services/task-svc/alembic.ini",
                "upgrade",
                "head",
            ],
            env=env,
        )

    processes = [
        start_process(
            "task-svc",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "services/task-svc",
                "--host",
                "0.0.0.0",
                "--port",
                "8011",
                "--reload",
            ],
            env=env,
        ),
        start_process(
            "model-svc",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "services/model-svc",
                "--host",
                "0.0.0.0",
                "--port",
                "8012",
                "--reload",
            ],
            env=env,
        ),
        start_process(
            "agent-svc",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "services/agent-svc",
                "--host",
                "0.0.0.0",
                "--port",
                "8013",
                "--reload",
            ],
            env=env,
        ),
        start_process(
            "knowledge-base-svc",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "services/knowledge-base-svc",
                "--host",
                "0.0.0.0",
                "--port",
                "8014",
                "--reload",
            ],
            env=env,
        ),
        start_process(
            "agent-worker",
            [sys.executable, "workers/agent-worker/app/main.py"],
            env=env,
        ),
    ]

    print("\nPhase 1-4 stack is starting. API: http://127.0.0.1:8011", flush=True)
    print("model-svc: http://127.0.0.1:8012", flush=True)
    print("agent-svc: http://127.0.0.1:8013", flush=True)
    print("knowledge-base-svc: http://127.0.0.1:8014", flush=True)
    print(
        "Press Ctrl+C to stop task-svc, model-svc, agent-svc, knowledge-base-svc and agent-worker.",
        flush=True,
    )
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_processes(processes)

    return next((process.returncode or 0 for process in processes if process.returncode), 0)


if __name__ == "__main__":
    raise SystemExit(main())
