"""Validate matched Roman Urdu variants and RU-P draft diagnostics."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from src.data.rule_engine import (
    FieldResult,
    RuleTables,
    transform_field,
)


class InvariantViolation(ValueError):
    """A dataset row or generated variant violated a required invariant."""


def reject_draft_failures(items: Iterable[Mapping[str, Any]]) -> None:
    """Reject all rows explicitly marked as failed RU-P drafts."""
    for item in items:
        notes = item.get("notes")
        if isinstance(notes, str) and notes.startswith("DRAFT_FAILED:"):
            item_id = item.get("item_id", "<unknown>")
            raise InvariantViolation(
                f"item {item_id}: invariant DRAFT_FAILED row rejection"
            )


def _field_value(item: Mapping[str, Any], field: str) -> str:
    if field == "question":
        value = item.get("question")
    else:
        option_index = int(field.removeprefix("options[")[:-1])
        options = item.get("options")
        value = options[option_index] if isinstance(options, list) and option_index < len(options) else None
    if not isinstance(value, str):
        raise InvariantViolation(
            f"item {item.get('item_id', '<unknown>')}, field {field}: invariant non-empty text type"
        )
    return value


def _token_count(text: str) -> int:
    return len(text.split())


def _nonletter_layout(text: str) -> tuple[tuple[bool, str | None], ...]:
    """Keep punctuation and digits fixed between letter runs."""
    layout: list[tuple[bool, str | None]] = []
    cursor = 0
    while cursor < len(text):
        is_letter = text[cursor].isalpha()
        end = cursor + 1
        while end < len(text) and text[end].isalpha() == is_letter:
            end += 1
        layout.append((is_letter, None if is_letter else text[cursor:end]))
        cursor = end
    return tuple(layout)


def _protected_sequence(text: str, protected_tokens: Sequence[str]) -> tuple[str, ...]:
    spans: list[tuple[int, int, str]] = []
    for token in dict.fromkeys(protected_tokens):
        if not token:
            raise ValueError("protected_tokens may not contain empty strings")
        start = 0
        while True:
            start = text.find(token, start)
            if start < 0:
                break
            spans.append((start, start + len(token), token))
            start += len(token)
    return tuple(span[2] for span in sorted(spans))


def validate_field_result(
    source_text: str,
    result: FieldResult,
    item_id: str,
    field: str,
    known_op_ids: frozenset[str],
) -> None:
    """Validate token provenance, operation IDs, protected text, and character invariants."""
    source_tokens = source_text.split()
    output_tokens = result.text.split()
    if len(source_tokens) != len(output_tokens):
        raise InvariantViolation(
            f"item {item_id}, field {field}: invariant whitespace token count"
        )
    if len(result.tokens) != len(source_tokens):
        raise InvariantViolation(
            f"item {item_id}, field {field}: invariant token provenance count"
        )
    for index, (source_token, output_token, record) in enumerate(
        zip(source_tokens, output_tokens, result.tokens)
    ):
        if (
            record.token_index != index
            or record.source_token != source_token
            or record.output_token != output_token
        ):
            raise InvariantViolation(
                f"item {item_id}, field {field}, token_index {index}: "
                "invariant positional provenance"
            )
        if not record.op_ids and source_token != output_token:
            raise InvariantViolation(
                f"item {item_id}, field {field}, token_index {index}: "
                "invariant untouched token changed"
            )
        unknown = set(record.op_ids) - known_op_ids
        if unknown:
            raise InvariantViolation(
                f"item {item_id}, field {field}, token_index {index}: "
                f"invariant unknown op_id {sorted(unknown)[0]}"
            )
        if _nonletter_layout(source_token) != _nonletter_layout(output_token):
            raise InvariantViolation(
                f"item {item_id}, field {field}, token_index {index}: "
                "invariant non-letter characters"
            )

    for span in result.protected_spans:
        if span.source_text != span.output_text:
            raise InvariantViolation(
                f"item {item_id}, field {field}, token_index {span.token_index}: "
                "invariant protected token unchanged "
                f"({','.join(span.pattern_ids)})"
            )


def validate_variant_group(
    rup_item: Mapping[str, Any],
    variants: Mapping[str, Mapping[str, Any]],
    tables: RuleTables,
    protected_tokens: Sequence[str] = (),
) -> None:
    """Validate RU-R and RU-X against RU-P and re-run transformations for stability."""
    item_id = str(rup_item.get("item_id", "<unknown>"))
    reject_draft_failures((rup_item, *variants.values()))
    if rup_item.get("condition") != "RU-P":
        raise InvariantViolation(f"item {item_id}: invariant RU-P reference condition")
    if set(variants) != {"RU-R", "RU-X"}:
        raise InvariantViolation(
            f"item {item_id}: invariant requires RU-R and RU-X variants"
        )
    reference_options = rup_item.get("options")
    if not isinstance(reference_options, list):
        raise InvariantViolation(f"item {item_id}: invariant options list")

    for variant, item in variants.items():
        if item.get("item_id") != rup_item.get("item_id"):
            raise InvariantViolation(f"item {item_id}: invariant item identity")
        if item.get("condition") != variant:
            raise InvariantViolation(f"item {item_id}: invariant condition {variant}")
        if item.get("gold") != rup_item.get("gold"):
            raise InvariantViolation(f"item {item_id}: invariant gold unchanged")
        options = item.get("options")
        if not isinstance(options, list) or len(options) != len(reference_options):
            raise InvariantViolation(f"item {item_id}: invariant option count and order")

        fields = ["question"] + [
            f"options[{index}]" for index in range(len(reference_options))
        ]
        for field in fields:
            source_text = _field_value(rup_item, field)
            actual_text = _field_value(item, field)
            first = transform_field(
                source_text, item_id, field, variant, tables, protected_tokens
            )
            repeated = transform_field(
                source_text, item_id, field, variant, tables, protected_tokens
            )
            if first != repeated:
                raise InvariantViolation(
                    f"item {item_id}, field {field}: invariant deterministic output"
                )
            if first.text != actual_text:
                invariant = (
                    "engine output/option order"
                    if field.startswith("options[")
                    else "engine output/provenance"
                )
                raise InvariantViolation(
                    f"item {item_id}, field {field}: invariant {invariant}"
                )
            validate_field_result(
                source_text, first, item_id, field, tables.op_ids
            )
            second_pass = transform_field(
                first.text, item_id, field, variant, tables, protected_tokens
            )
            if second_pass.text != first.text:
                raise InvariantViolation(
                    f"item {item_id}, field {field}: invariant idempotence"
                )


def validate_rup_proxy(
    nu_item: Mapping[str, Any],
    rup_item: Mapping[str, Any],
    protected_tokens: Sequence[str] = (),
) -> dict[str, Any]:
    """Return proxy diagnostics for RU-P versus NU; these are not invariant passes."""
    item_id = str(nu_item.get("item_id", "<unknown>"))
    reject_draft_failures((rup_item,))
    diagnostics: list[str] = []
    nu_options = nu_item.get("options")
    rup_options = rup_item.get("options")
    if not isinstance(nu_options, list) or not isinstance(rup_options, list):
        diagnostics.append("options: invalid option-list type")
    elif len(nu_options) != len(rup_options):
        diagnostics.append("options: option count differs; order cannot be checked")
    else:
        diagnostics.append("options: positional order assumed; semantic order is not machine-verifiable")
    if nu_item.get("gold") != rup_item.get("gold"):
        diagnostics.append("gold: differs")

    fields: list[tuple[str, Any, Any]] = [
        ("question", nu_item.get("question"), rup_item.get("question"))
    ]
    if isinstance(nu_options, list) and isinstance(rup_options, list):
        fields.extend(
            (f"options[{index}]", left, right)
            for index, (left, right) in enumerate(zip(nu_options, rup_options))
        )
    for field, nu_text, rup_text in fields:
        if not isinstance(nu_text, str) or not isinstance(rup_text, str):
            diagnostics.append(f"{field}: invalid text value")
            continue
        if _token_count(nu_text) != _token_count(rup_text):
            diagnostics.append(f"{field}: whitespace token count differs")
        nu_digits = "".join(char for char in nu_text if char.isdecimal())
        rup_digits = "".join(char for char in rup_text if char.isdecimal())
        if nu_digits != rup_digits:
            diagnostics.append(f"{field}: digit sequence differs")
        if _protected_sequence(nu_text, protected_tokens) != _protected_sequence(
            rup_text, protected_tokens
        ):
            diagnostics.append(f"{field}: protected token sequence differs")

    return {
        "item_id": item_id,
        "status": "proxy",
        "diagnostics": diagnostics,
    }
