"""Deterministic agent definitions for early orchestration."""

from __future__ import annotations

from app.harness import AgentDefinition

CONTENT_AGENT = AgentDefinition(
    name="content-agent",
    role="Draft and revise structured content.",
)
RESEARCH_AGENT = AgentDefinition(
    name="research-agent",
    role="Plan source collection and synthesize findings.",
)
ARXIV_AGENT = AgentDefinition(
    name="arxiv-agent",
    role="Collect and summarize research papers.",
)
INTERVIEW_AGENT = AgentDefinition(
    name="interview-agent",
    role="Prepare interview questions and review answers.",
)
FILE_AGENT = AgentDefinition(
    name="file-agent",
    role="Parse files and extract reusable context.",
)
PLANNER_AGENT = AgentDefinition(
    name="planner-agent",
    role="Route unknown task types safely.",
)
