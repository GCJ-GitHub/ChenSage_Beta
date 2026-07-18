"""create knowledge base tables

Revision ID: 0001_create_knowledge_tables
Revises:
Create Date: 2026-07-18 19:45:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from app.core.settings import settings
from sqlalchemy.dialects import postgresql

revision = "0001_create_knowledge_tables"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = settings.database_schema


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))
    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index(
        "ix_knowledge_items_created_at",
        "knowledge_items",
        ["created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_items_quality_score",
        "knowledge_items",
        ["quality_score"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_items_source_type",
        "knowledge_items",
        ["source_type"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_items_status",
        "knowledge_items",
        ["status"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_items_tags",
        "knowledge_items",
        ["tags"],
        schema=SCHEMA,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_knowledge_items_task_type",
        "knowledge_items",
        ["task_type"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_items_updated_at",
        "knowledge_items",
        ["updated_at"],
        schema=SCHEMA,
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("item_id", sa.String(length=36), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            [f"{SCHEMA}.knowledge_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_chunks_created_at",
        "knowledge_chunks",
        ["created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_chunks_item_id",
        "knowledge_chunks",
        ["item_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_chunks_ordinal",
        "knowledge_chunks",
        ["ordinal"],
        schema=SCHEMA,
    )

    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("item_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("uri", sa.String(length=1000), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            [f"{SCHEMA}.knowledge_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_sources_created_at",
        "knowledge_sources",
        ["created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_sources_item_id",
        "knowledge_sources",
        ["item_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_sources_source_type",
        "knowledge_sources",
        ["source_type"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_sources_source_type", table_name="knowledge_sources", schema=SCHEMA)
    op.drop_index("ix_knowledge_sources_item_id", table_name="knowledge_sources", schema=SCHEMA)
    op.drop_index("ix_knowledge_sources_created_at", table_name="knowledge_sources", schema=SCHEMA)
    op.drop_table("knowledge_sources", schema=SCHEMA)

    op.drop_index("ix_knowledge_chunks_ordinal", table_name="knowledge_chunks", schema=SCHEMA)
    op.drop_index("ix_knowledge_chunks_item_id", table_name="knowledge_chunks", schema=SCHEMA)
    op.drop_index("ix_knowledge_chunks_created_at", table_name="knowledge_chunks", schema=SCHEMA)
    op.drop_table("knowledge_chunks", schema=SCHEMA)

    op.drop_index("ix_knowledge_items_updated_at", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_task_type", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_tags", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_status", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_source_type", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_quality_score", table_name="knowledge_items", schema=SCHEMA)
    op.drop_index("ix_knowledge_items_created_at", table_name="knowledge_items", schema=SCHEMA)
    op.drop_table("knowledge_items", schema=SCHEMA)
