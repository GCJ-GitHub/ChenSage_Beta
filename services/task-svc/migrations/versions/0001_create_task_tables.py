"""create task lifecycle tables

Revision ID: 0001_create_task_tables
Revises:
Create Date: 2026-07-11 19:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from app.core.settings import settings
from sqlalchemy.dialects import postgresql

revision = "0001_create_task_tables"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = settings.database_schema


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_type", sa.String(length=80), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("template", sa.String(length=120), nullable=True),
        sa.Column("output_format", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"], schema=SCHEMA)
    op.create_index("ix_tasks_status", "tasks", ["status"], schema=SCHEMA)
    op.create_index("ix_tasks_task_type", "tasks", ["task_type"], schema=SCHEMA)

    op.create_table(
        "task_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], [f"{SCHEMA}.tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_task_events_created_at", "task_events", ["created_at"], schema=SCHEMA)
    op.create_index("ix_task_events_event_type", "task_events", ["event_type"], schema=SCHEMA)
    op.create_index("ix_task_events_task_id", "task_events", ["task_id"], schema=SCHEMA)

    op.create_table(
        "task_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["task_id"], [f"{SCHEMA}.tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uq_task_results_task_id"),
        schema=SCHEMA,
    )
    op.create_index("ix_task_results_created_at", "task_results", ["created_at"], schema=SCHEMA)
    op.create_index("ix_task_results_task_id", "task_results", ["task_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_task_results_task_id", table_name="task_results", schema=SCHEMA)
    op.drop_index("ix_task_results_created_at", table_name="task_results", schema=SCHEMA)
    op.drop_table("task_results", schema=SCHEMA)

    op.drop_index("ix_task_events_task_id", table_name="task_events", schema=SCHEMA)
    op.drop_index("ix_task_events_event_type", table_name="task_events", schema=SCHEMA)
    op.drop_index("ix_task_events_created_at", table_name="task_events", schema=SCHEMA)
    op.drop_table("task_events", schema=SCHEMA)

    op.drop_index("ix_tasks_task_type", table_name="tasks", schema=SCHEMA)
    op.drop_index("ix_tasks_status", table_name="tasks", schema=SCHEMA)
    op.drop_index("ix_tasks_created_at", table_name="tasks", schema=SCHEMA)
    op.drop_table("tasks", schema=SCHEMA)
