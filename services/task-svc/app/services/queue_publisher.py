"""RabbitMQ publisher for task dispatch."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import pika


@dataclass(frozen=True, slots=True)
class QueueSettings:
    host: str = os.getenv("RABBITMQ_HOST", "localhost")
    port: int = int(os.getenv("RABBITMQ_PORT", "5672"))
    user: str = os.getenv("RABBITMQ_USER", "chensage")
    password: str = os.getenv("RABBITMQ_PASSWORD", "chensage_dev_password")
    queue_name: str = os.getenv("AGENT_WORKER_QUEUE", "agent.tasks")


class TaskQueuePublisher:
    def __init__(self, settings: QueueSettings | None = None) -> None:
        self.settings = settings or QueueSettings()

    def publish(self, message: dict[str, Any]) -> None:
        credentials = pika.PlainCredentials(self.settings.user, self.settings.password)
        parameters = pika.ConnectionParameters(
            host=self.settings.host,
            port=self.settings.port,
            credentials=credentials,
            heartbeat=30,
            blocked_connection_timeout=10,
        )
        connection = pika.BlockingConnection(parameters)
        try:
            channel = connection.channel()
            channel.queue_declare(queue=self.settings.queue_name, durable=True)
            channel.basic_publish(
                exchange="",
                routing_key=self.settings.queue_name,
                body=json.dumps(message).encode("utf-8"),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=pika.DeliveryMode.Persistent,
                ),
            )
        finally:
            connection.close()


task_queue_publisher = TaskQueuePublisher()

