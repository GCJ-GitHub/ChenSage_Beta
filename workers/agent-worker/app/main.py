"""Minimal phase 0 worker entrypoint.

The real RabbitMQ consumer starts in phase 1. For now this entrypoint makes the
worker boundary executable and documents the environment it will use.
"""

from __future__ import annotations

import os


def main() -> None:
    queue_name = os.getenv("AGENT_WORKER_QUEUE", "agent.tasks")
    print(f"agent-worker ready; queue={queue_name}")


if __name__ == "__main__":
    main()
