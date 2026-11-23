"""Apply the approved deterministic RU-R and RU-X rule tables."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


WORD_MAP_HEADER = ("ru_p", "ru_r", "op_id", "note")
RULE_HEADER = ("order", "pattern", "replacement", "op_id", "note")
PROTECTED_HEADER = ("pattern_id", "kind", "pattern", "note")
LEXICON_HEADER = ("urdu_word", "ru_p", "note")
VARIANTS = {"RU-R", "RU-X"}
TOKEN_PATTERN = re.compile(r"\S+")


class RuleEngineError(ValueError):
    """A rule or transformation violated the engine contract."""


@dataclass(frozen=True)
class WordMapRule:
    source: str
    replacement: str
    op_id: str


@dataclass(frozen=True)
class RegexRule:
    order: int
    pattern: str
    replacement: str
    op_id: str


@dataclass(frozen=True)
class ProtectedPattern:
    pattern_id: str
    kind: str
    pattern: str


@dataclass(frozen=True)
class RuleTables:
    word_maps: Mapping[str, WordMapRule]
    regex_rules: Mapping[str, tuple[RegexRule, ...]]
    protected_patterns: tuple[ProtectedPattern, ...]

    @property
    def op_ids(self) -> frozenset[str]:
        """Return all operation IDs declared by the loaded rule tables."""
        return frozenset(
            [rule.op_id for rule in self.word_maps.values()]
            + [rule.op_id for rules in self.regex_rules.values() for rule in rules]
        )


@dataclass(frozen=True)
class TokenProvenance:
    token_index: int
    source_token: str
    output_token: str
    op_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProtectedSpanResult:
    token_index: int
    source_text: str
    output_text: str
    pattern_ids: tuple[str, ...]


@dataclass(frozen=True)
class FieldResult:
    source_text: str
    text: str
    tokens: tuple[TokenProvenance, ...]
    protected_spans: tuple[ProtectedSpanResult, ...]

    @property
    def unmatched_words(self) -> tuple[str, ...]:
        """Return source tokens that were not touched by any operation."""
        return tuple(token.source_token for token in self.tokens if not token.op_ids)


@dataclass(frozen=True)
class ItemTransformResult:
    item: dict[str, Any]
    fields: Mapping[str, FieldResult]

    @property
    def variant_equals_reference(self) -> bool:
        """Report whether every transformed item field equals its RU-P source."""
        return all(
            result.source_text == result.text
            for result in self.fields.values()
        )

    @property
    def unmatched_words(self) -> Mapping[str, tuple[str, ...]]:
        """Report untouched source tokens by field."""
        return {
            field: result.unmatched_words
            for field, result in self.fields.items()
        }


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    pattern_ids: tuple[str, ...]


def _read_csv(path: Path, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a UTF-8 CSV and require its exact documented header."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise RuleEngineError(
                f"{path} must have exact header {','.join(expected_header)}"
            )
        rows = [dict(row) for row in reader]
    for line_number, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            raise RuleEngineError(f"{path} has malformed CSV row at line {line_number}")
    return rows


def _active_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ignore rows explicitly marked as examples."""
    return [
        row for row in rows
        if not (row.get("note") or "").startswith("EXAMPLE")
    ]


def load_rule_tables(rule_dir: Path) -> RuleTables:
    """Load RU-R/RU-X tables and protected patterns from a rules directory."""
    word_rows = _active_rows(
        _read_csv(rule_dir / "ru_r_wordmap.csv", WORD_MAP_HEADER)
    )
    ru_r_rows = _active_rows(
        _read_csv(rule_dir / "ru_r_rules.csv", RULE_HEADER)
    )
    ru_x_rows = _active_rows(
        _read_csv(rule_dir / "ru_x_rules.csv", RULE_HEADER)
    )
    protected_rows = _active_rows(
        _read_csv(rule_dir / "protected_patterns.csv", PROTECTED_HEADER)
    )

    word_maps: dict[str, WordMapRule] = {}
    for row in word_rows:
        source = row["ru_p"]
        if (
            not source
            or any(char.isspace() for char in source)
            or not row["ru_r"]
            or not row["op_id"]
        ):
            raise RuleEngineError("Word-map rows require non-empty values and op_id")
        if source in word_maps:
            raise RuleEngineError(f"Duplicate RU-P word-map entry: {source!r}")
        word_maps[source] = WordMapRule(source, row["ru_r"], row["op_id"])

    regex_rules: dict[str, tuple[RegexRule, ...]] = {}
    for variant, rows in (("RU-R", ru_r_rows), ("RU-X", ru_x_rows)):
        parsed: list[RegexRule] = []
        seen_orders: set[int] = set()
        for row in rows:
            try:
                order = int(row["order"])
            except ValueError as exc:
                raise RuleEngineError(
                    f"{variant} rule order must be an integer: {row['order']!r}"
                ) from exc
            if order in seen_orders:
                raise RuleEngineError(f"{variant} has duplicate rule order {order}")
            if not row["pattern"] or not row["op_id"]:
                raise RuleEngineError(
                    f"{variant} rule {order} requires a pattern and op_id"
                )
            seen_orders.add(order)
            parsed.append(
                RegexRule(order, row["pattern"], row["replacement"], row["op_id"])
            )
        regex_rules[variant] = tuple(sorted(parsed, key=lambda rule: rule.order))

    protected_patterns: list[ProtectedPattern] = []
    seen_ids: set[str] = set()
    for row in protected_rows:
        pattern_id = row["pattern_id"]
        kind = row["kind"]
        pattern = row["pattern"]
        if not pattern_id or pattern_id in seen_ids:
            raise RuleEngineError(f"Protected pattern_id must be unique and non-empty: {pattern_id!r}")
        if kind not in {"regex", "literal"}:
            raise RuleEngineError(
                f"Protected pattern {pattern_id!r} kind must be 'regex' or 'literal'"
            )
        if not pattern:
            raise RuleEngineError(f"Protected pattern {pattern_id!r} is empty")
        seen_ids.add(pattern_id)
        protected_patterns.append(ProtectedPattern(pattern_id, kind, pattern))

    return RuleTables(word_maps, regex_rules, tuple(protected_patterns))


def _reserved_placeholder_char(char: str) -> bool:
    codepoint = ord(char)
    return codepoint in {0xE000, 0xE001} or 0xE100 <= codepoint <= 0xE10F


def _collect_spans(
    text: str,
    item_id: str,
    field: str,
    patterns: Sequence[ProtectedPattern],
    protected_tokens: Sequence[str],
) -> list[_Span]:
    spans: list[_Span] = []
    for protected in patterns:
        try:
            expression = re.escape(protected.pattern) if protected.kind == "literal" else protected.pattern
            compiled = re.compile(expression, re.UNICODE)
        except re.error as exc:
            raise RuleEngineError(
                f"item {item_id}, field {field}, pattern_id {protected.pattern_id}: "
                f"invalid protected regex: {exc}"
            ) from exc
        if compiled.search("") is not None:
            raise RuleEngineError(
                f"item {item_id}, field {field}, pattern_id {protected.pattern_id}: "
                "protected pattern matches the empty string"
            )
        for match in compiled.finditer(text):
            if match.start() == match.end():
                raise RuleEngineError(
                    f"item {item_id}, field {field}, pattern_id {protected.pattern_id}: "
                    "protected pattern produced an empty span"
                )
            spans.append(
                _Span(match.start(), match.end(), (protected.pattern_id,))
            )

    for protected_token in protected_tokens:
        if not protected_token:
            raise RuleEngineError(
                f"item {item_id}, field {field}: protected_tokens may not contain empty strings"
            )
        start = 0
        while True:
            start = text.find(protected_token, start)
            if start < 0:
                break
            spans.append(
                _Span(start, start + len(protected_token), ("protected_tokens",))
            )
            start += len(protected_token)

    spans.sort(key=lambda span: (span.start, span.end))
    merged: list[_Span] = []
    for span in spans:
        if merged and span.start <= merged[-1].end:
            previous = merged[-1]
            merged[-1] = _Span(
                previous.start,
                max(previous.end, span.end),
                tuple(dict.fromkeys(previous.pattern_ids + span.pattern_ids)),
            )
        else:
            merged.append(span)
    return merged


def _make_placeholder(index: int) -> str:
    """Encode an index using reserved private-use code points."""
    digits = f"{index:X}"
    return "\ue000" + "".join(chr(0xE100 + int(digit, 16)) for digit in digits) + "\ue001"


def _apply_word_map(
    token: str,
    word_maps: Mapping[str, WordMapRule],
) -> tuple[str, tuple[str, ...]]:
    applied: list[str] = []
    output = token
    for source, rule in word_maps.items():
        boundary_pattern = re.compile(
            rf"(?<!\w){re.escape(source)}(?!\w)", re.UNICODE
        )

        def replace(_: re.Match[str], replacement: str = rule.replacement) -> str:
            return replacement

        output, count = boundary_pattern.subn(replace, output)
        if count:
            applied.append(rule.op_id)
    return output, tuple(applied)


def _apply_regex_rules(
    token: str,
    rules: Sequence[RegexRule],
    item_id: str,
    field: str,
) -> tuple[str, tuple[str, ...]]:
    output = token
    applied: list[str] = []
    for rule in rules:
        try:
            compiled = re.compile(rule.pattern, re.UNICODE)
        except re.error as exc:
            raise RuleEngineError(
                f"item {item_id}, field {field}, rule order {rule.order}: "
                f"invalid regex: {exc}"
            ) from exc
        if compiled.search("") is not None:
            raise RuleEngineError(
                f"item {item_id}, field {field}, rule order {rule.order}: "
                "regex matches the empty string"
            )
        matches = list(compiled.finditer(output))
        if any(match.start() == match.end() for match in matches):
            raise RuleEngineError(
                f"item {item_id}, field {field}, rule order {rule.order}: "
                "regex produced an empty span"
            )
        valid_matches = [
            match for match in matches
            if (match.start() == 0 or not (output[match.start() - 1].isalnum()
                                           or output[match.start() - 1] == "_"))
            and (match.end() == len(output) or not (output[match.end()].isalnum()
                                                    or output[match.end()] == "_"))
        ]
        if valid_matches:
            pieces: list[str] = []
            cursor = 0
            for match in valid_matches:
                pieces.append(output[cursor:match.start()])
                try:
                    pieces.append(match.expand(rule.replacement))
                except re.error as exc:
                    raise RuleEngineError(
                        f"item {item_id}, field {field}, rule order {rule.order}: "
                        f"invalid replacement: {exc}"
                    ) from exc
                cursor = match.end()
            pieces.append(output[cursor:])
            output = "".join(pieces)
            applied.append(rule.op_id)
    return output, tuple(applied)


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


def transform_field(
    text: str,
    item_id: str,
    field: str,
    variant: str,
    tables: RuleTables,
    protected_tokens: Sequence[str] = (),
) -> FieldResult:
    """Transform one text field and return per-token provenance and protection data."""
    if variant not in VARIANTS:
        raise ValueError(f"Unsupported variant: {variant}")
    if any(_reserved_placeholder_char(char) for char in text):
        raise RuleEngineError(
            f"item {item_id}, field {field}: input contains a private-use character"
        )

    spans = _collect_spans(
        text, item_id, field, tables.protected_patterns, protected_tokens
    )
    regex_rules = tables.regex_rules[variant]
    output_parts: list[str] = []
    token_records: list[TokenProvenance] = []
    cursor = 0
    placeholder_index = 0

    for index, match in enumerate(TOKEN_PATTERN.finditer(text)):
        output_parts.append(text[cursor:match.start()])
        source_token = match.group()
        token_spans = [
            span for span in spans
            if span.start < match.end() and span.end > match.start()
        ]
        token_pieces: list[str] = []
        token_placeholders: dict[str, tuple[str, tuple[str, ...]]] = {}
        token_cursor = match.start()
        for span in token_spans:
            segment_start = max(span.start, match.start())
            segment_end = min(span.end, match.end())
            token_pieces.append(text[token_cursor:segment_start])
            placeholder = _make_placeholder(placeholder_index)
            placeholder_index += 1
            token_pieces.append(placeholder)
            token_placeholders[placeholder] = (
                text[segment_start:segment_end],
                span.pattern_ids,
            )
            token_cursor = segment_end
        token_pieces.append(text[token_cursor:match.end()])
        masked_token = "".join(token_pieces)
        if variant == "RU-R":
            mapped, map_ops = _apply_word_map(masked_token, tables.word_maps)
        else:
            mapped, map_ops = masked_token, ()
        transformed, regex_ops = _apply_regex_rules(
            mapped, regex_rules, item_id, field
        )
        restored_token = transformed
        for placeholder, (protected_text, pattern_ids) in token_placeholders.items():
            if restored_token.count(placeholder) != 1:
                raise RuleEngineError(
                    f"item {item_id}, field {field}, pattern_id "
                    f"{','.join(pattern_ids)}: rule altered a protected placeholder"
                )
            restored_token = restored_token.replace(placeholder, protected_text)
        if any(_reserved_placeholder_char(char) for char in restored_token):
            raise RuleEngineError(
                f"item {item_id}, field {field}: a rule introduced a private-use character"
            )
        output_parts.append(restored_token)
        token_records.append(
            TokenProvenance(
                index,
                source_token,
                restored_token,
                tuple(dict.fromkeys(map_ops + regex_ops)),
            )
        )
        cursor = match.end()

    output_parts.append(text[cursor:])
    output = "".join(output_parts)
    for record in token_records:
        if _nonletter_layout(record.source_token) != _nonletter_layout(record.output_token):
            raise RuleEngineError(
                f"item {item_id}, field {field}, token_index {record.token_index}: "
                "non-letter characters changed"
            )
        if record.source_token != record.output_token and not record.op_ids:
            raise RuleEngineError(
                f"item {item_id}, field {field}, token_index {record.token_index}: "
                "changed token has no operation ID"
            )

    protected_results = tuple(
        ProtectedSpanResult(
            sum(
                token.end() <= span.start
                for token in TOKEN_PATTERN.finditer(text)
            ),
            text[span.start:span.end],
            text[span.start:span.end],
            span.pattern_ids,
        )
        for span in spans
    )
    return FieldResult(text, output, tuple(token_records), protected_results)


def transform_item(
    item: Mapping[str, Any],
    variant: str,
    tables: RuleTables,
    protected_tokens: Sequence[str] = (),
) -> ItemTransformResult:
    """Transform an RU-P item question and all options into one RU variant."""
    item_id = str(item.get("item_id", "<unknown>"))
    if item.get("condition") != "RU-P":
        raise RuleEngineError(
            f"item {item_id}: invariant RU-P source condition required for {variant}"
        )
    question = item.get("question")
    options = item.get("options")
    if not isinstance(question, str) or not isinstance(options, list):
        raise RuleEngineError(f"item {item_id}: question/options have invalid types")
    fields: dict[str, FieldResult] = {
        "question": transform_field(
            question, item_id, "question", variant, tables, protected_tokens
        )
    }
    transformed_options: list[str] = []
    for index, option in enumerate(options):
        if not isinstance(option, str):
            raise RuleEngineError(f"item {item_id}: option {index} is not text")
        field = f"options[{index}]"
        result = transform_field(
            option, item_id, field, variant, tables, protected_tokens
        )
        fields[field] = result
        transformed_options.append(result.text)
    row = dict(item)
    row["condition"] = variant
    row["question"] = fields["question"].text
    row["options"] = transformed_options
    return ItemTransformResult(row, fields)
