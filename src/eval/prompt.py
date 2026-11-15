"""Build a condition-specific prompt and hash the exact rendered text."""

from __future__ import annotations

import hashlib
from pathlib import Path
from string import Formatter
from typing import Any


class PromptTemplateError(ValueError):
    """Raised when the agreed prompt template is unavailable or malformed."""


REQUIRED_FIELDS = {"letters", "question", "options"}


def letters_for_options(option_count: int) -> list[str]:
    """Return A-Z labels for a positive option count; reject unsupported counts."""
    if not 1 <= option_count <= 26:
        raise ValueError("An item must have between 1 and 26 options.")
    return [chr(ord("A") + index) for index in range(option_count)]


def _format_letters(letters: list[str]) -> str:
    if len(letters) == 1:
        return letters[0]
    if len(letters) == 2:
        return f"{letters[0]} or {letters[1]}"
    return f"{', '.join(letters[:-1])}, or {letters[-1]}"


def build_prompt(
    item: dict[str, Any],
    condition: str,
    template_path: str | Path,
) -> tuple[str, str]:
    """Render the approved template for one item/condition and return prompt, SHA-256."""
    if item.get("condition") != condition:
        raise ValueError(
            f"Item '{item.get('item_id', '<unknown>')}' has condition "
            f"{item.get('condition')!r}, not requested condition {condition!r}."
        )
    question = item.get("question")
    options = item.get("options")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Item question must be non-empty text.")
    if not isinstance(options, list) or not options or not all(
        isinstance(option, str) and option.strip() for option in options
    ):
        raise ValueError("Item options must be a non-empty list of non-empty strings.")

    path = Path(template_path)
    try:
        template = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptTemplateError(f"Cannot read prompt template {path}: {exc}") from exc
    if "TODO" in template.upper():
        raise PromptTemplateError(
            f"Prompt template {path} still contains TODO; agree its text at Gate G0."
        )
    try:
        fields = {
            field_name
            for _, field_name, _, _ in Formatter().parse(template)
            if field_name is not None
        }
    except ValueError as exc:
        raise PromptTemplateError(f"Malformed prompt template {path}: {exc}") from exc
    if fields != REQUIRED_FIELDS:
        raise PromptTemplateError(
            f"Prompt template {path} must contain exactly {sorted(REQUIRED_FIELDS)}; "
            f"found {sorted(fields)}."
        )

    letters = letters_for_options(len(options))
    rendered = template.format(
        letters=_format_letters(letters),
        question=question,
        options="\n".join(
            f"{letter}) {option}" for letter, option in zip(letters, options)
        ),
    )
    prompt_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    return rendered, prompt_hash
