"""Prompt template registry backed by config/prompts YAML files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from app.schemas.prompts import PromptTemplateResponse, PromptVariableDefinition

PROMPT_ROOT = Path(__file__).resolve().parents[4] / "config" / "prompts"
VARIABLE_PATTERN = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")

TASK_TYPE_CATEGORY_ALIASES = {
    "content": "content",
    "content_generation": "content",
    "content_rewrite": "content",
    "essay": "content",
    "novel": "content",
    "speech_script": "content",
    "standup_script": "content",
    "research": "research",
    "research_report": "research",
    "information_collection": "research",
    "information_research": "research",
    "arxiv": "arxiv",
    "arxiv_daily": "arxiv",
    "interview": "interview",
    "mock_interview": "interview",
    "interview_session": "interview",
    "conversation": "conversation",
    "conversation_routing": "conversation",
    "evaluation": "evaluation",
    "content_evaluation": "evaluation",
}


class PromptTemplateNotFoundError(LookupError):
    """Raised when a prompt template cannot be resolved."""


class PromptRegistry:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or PROMPT_ROOT
        self._templates = self._load_templates()

    def list_templates(self, task_type: str | None = None) -> list[PromptTemplateResponse]:
        templates = sorted(self._templates.values(), key=lambda item: item.id)
        if task_type is None:
            return templates
        category = _category_for_task_type(task_type)
        return [
            template
            for template in templates
            if template.task_type == task_type or template.category == category
        ]

    def get_template(self, template_id: str) -> PromptTemplateResponse:
        template = self._templates.get(template_id)
        if template is None:
            raise PromptTemplateNotFoundError(template_id)
        return template

    def resolve(
        self,
        *,
        template_id: str | None,
        task_type: str,
    ) -> PromptTemplateResponse:
        if template_id:
            template = self._templates.get(template_id)
            if template is not None:
                return template
            by_name = next(
                (item for item in self._templates.values() if item.name == template_id),
                None,
            )
            if by_name is not None:
                return by_name
        candidates = self.list_templates(task_type=task_type)
        exact_candidates = [template for template in candidates if template.task_type == task_type]
        if exact_candidates:
            return exact_candidates[0]
        if candidates:
            return candidates[0]
        fallback = self._templates.get("generic.default") or next(
            iter(sorted(self._templates.values(), key=lambda item: item.id)),
            None,
        )
        if fallback is not None:
            return fallback
        raise PromptTemplateNotFoundError(template_id or task_type)

    def render(
        self,
        *,
        template: PromptTemplateResponse,
        values: dict[str, Any],
    ) -> tuple[str, list[str]]:
        missing: list[str] = []

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in values or values[name] in (None, ""):
                if name not in missing:
                    missing.append(name)
                return f"[[missing:{name}]]"
            return _stringify(values[name])

        return VARIABLE_PATTERN.sub(replace, template.template), missing

    def _load_templates(self) -> dict[str, PromptTemplateResponse]:
        templates: dict[str, PromptTemplateResponse] = {}
        if not self.root.exists():
            return templates
        for path in sorted(self.root.rglob("*.yaml")):
            template = self._load_template(path)
            templates[template.id] = template
        return templates

    def _load_template(self, path: Path) -> PromptTemplateResponse:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Prompt template must be a mapping: {path}")
        variables = {
            name: PromptVariableDefinition.model_validate(definition or {})
            for name, definition in dict(data.get("variables") or {}).items()
        }
        return PromptTemplateResponse(
            id=str(data["id"]),
            name=str(data.get("name") or data["id"]),
            task_type=str(data["task_type"]),
            category=path.parent.name,
            version=str(data.get("version") or "0.0.0"),
            variables=variables,
            template=str(data["template"]),
            source_path=path.relative_to(self.root).as_posix(),
        )


def build_template_values(
    *,
    task_type: str,
    goal: str,
    output_format: str | None,
    task_input: dict[str, Any],
) -> dict[str, Any]:
    values: dict[str, Any] = dict(task_input)
    values.setdefault("goal", goal)
    values.setdefault("topic", goal)
    values.setdefault("content_type", _category_for_task_type(task_type))
    values.setdefault("research_goal", goal)
    values.setdefault("user_goal", goal)
    values.setdefault("user_message", goal)
    values.setdefault("output_format", output_format or "Markdown")
    values.setdefault("audience", "未指定")
    values.setdefault("tone", "未指定")
    values.setdefault("length", task_input.get("set_length") or "未指定")
    values.setdefault("set_length", task_input.get("length") or "未指定")
    values.setdefault("rewrite_instruction", goal)
    values.setdefault("sources", task_input.get("source") or task_input.get("urls") or [])
    values.setdefault("resume_summary", task_input.get("resume") or "未提供")
    values.setdefault("job_description", task_input.get("job_description") or "未提供")
    values.setdefault("interview_focus", task_input.get("focus") or "未指定")
    values.setdefault("research_direction", goal)
    values.setdefault("keywords", task_input.get("keywords") or [])
    values.setdefault("categories", task_input.get("categories") or [])
    values.setdefault("date_range", task_input.get("date_range") or "未指定")
    values.setdefault("available_task_types", sorted(TASK_TYPE_CATEGORY_ALIASES))
    values.setdefault("generated_content", task_input.get("generated_content") or "待生成")
    values.setdefault("evaluation_context", task_input.get("evaluation_context") or "未指定")
    return values


def _category_for_task_type(task_type: str) -> str:
    return TASK_TYPE_CATEGORY_ALIASES.get(task_type, task_type)


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int | float | bool):
        return str(value)
    return json.dumps(value, ensure_ascii=False, indent=2)
