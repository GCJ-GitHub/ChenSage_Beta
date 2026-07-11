"""Configuration boundary for task-svc."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskServiceSettings:
    database_url: str
    database_schema: str

    @classmethod
    def from_env(cls) -> TaskServiceSettings:
        database_schema = os.getenv("TASK_DATABASE_SCHEMA", "task_svc")
        explicit_url = os.getenv("TASK_DATABASE_URL")
        if explicit_url:
            return cls(database_url=explicit_url, database_schema=database_schema)

        user = os.getenv("POSTGRES_USER", "chensage")
        password = os.getenv("POSTGRES_PASSWORD", "chensage_dev_password")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "chensage")
        return cls(
            database_url=f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}",
            database_schema=database_schema,
        )


settings = TaskServiceSettings.from_env()
