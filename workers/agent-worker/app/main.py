"""RabbitMQ worker for the phase 1 task execution loop."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pika

WORKER_ROOT = Path(__file__).resolve().parents[1]
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

from app.executors import execute_task  # noqa: E402


@dataclass(frozen=True, slots=True)
class WorkerSettings:
    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "127.0.0.1")
    rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "chensage")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "chensage_dev_password")
    queue_name: str = os.getenv("AGENT_WORKER_QUEUE", "agent.tasks")
    task_svc_url: str = os.getenv("TASK_SVC_URL", "http://127.0.0.1:8011")


class TaskClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(trust_env=False)

    def event(
        self,
        task_id: str,
        event_type: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.client.post(
            f"{self.base_url}/tasks/{task_id}/events",
            json={"event_type": event_type, "message": message, "data": data or {}},
            timeout=10,
        ).raise_for_status()

    def update(
        self,
        task_id: str,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        event_type: str,
        message: str,
    ) -> None:
        payload: dict[str, Any] = {
            "status": status,
            "event": {"event_type": event_type, "message": message, "data": {}},
        }
        if result is not None:
            payload["result"] = result
        if error is not None:
            payload["error"] = error
        self.client.patch(
            f"{self.base_url}/tasks/{task_id}",
            json=payload,
            timeout=10,
        ).raise_for_status()


def handle_message(task_client: TaskClient, message: dict[str, Any]) -> None:
    task_id = str(message["task_id"])
    result = execute_task(message)
    task_client.update(
        task_id,
        status="running",
        event_type="task.started",
        message=f"agent-worker started {result.executor}.",
    )
    task_client.event(
        task_id,
        "task.executor_selected",
        f"Worker selected {result.executor} for task type {result.task_type}.",
        {"worker": "agent-worker", "executor": result.executor},
    )
    task_client.update(
        task_id,
        status="succeeded",
        result=result.to_payload(),
        event_type="task.completed",
        message=f"agent-worker finished {result.executor}.",
    )


def main() -> None:
    settings = WorkerSettings()
    task_client = TaskClient(settings.task_svc_url)
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=settings.queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)

    def on_message(
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        del properties
        try:
            message = json.loads(body.decode("utf-8"))
            handle_message(task_client, message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            try:
                task_id = json.loads(body.decode("utf-8")).get("task_id")
                if task_id:
                    task_client.update(
                        str(task_id),
                        status="failed",
                        error=str(exc),
                        event_type="task.failed",
                        message="agent-worker failed while executing the task.",
                    )
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=settings.queue_name, on_message_callback=on_message)
    print(f"agent-worker consuming queue={settings.queue_name} task_svc={settings.task_svc_url}")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
