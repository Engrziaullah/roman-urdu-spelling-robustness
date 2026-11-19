"""Compute character-level distances between matched RU variants."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.data.invariants import reject_draft_failures


ROOT = Path(__file__).resolve().parents[2]
CONDITIONS = ("RU-P", "RU-R", "RU-X")
PAIRS = (("RU-P", "RU-R"), ("RU-P", "RU-X"), ("RU-R", "RU-X"))
CSV_HEADER = (
    "variant_pair",
    "n_items",
    "n_fields",
    "mean_char_edit_distance",
    "mean_normalized_edit_distance",
    "share_items_identical",
    "share_fields_identical",
)


def levenshtein_distance(left: str, right: str) -> int:
    """Return Levenshtein distance over Python Unicode code points."""
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_char != right_char),
                )
            )
        previous = current
    return previous[-1]


def _item_fields(item: Mapping[str, Any], item_id: str) -> list[str]:
    question = item.get("question")
    options = item.get("options")
    if not isinstance(question, str) or not isinstance(options, list):
        raise ValueError(f"item {item_id}: question/options have invalid types")
    if not all(isinstance(option, str) for option in options):
        raise ValueError(f"item {item_id}: every option must be text")
    return [question, *options]


def _group_items(
    items: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Mapping[str, Any]]]:
    """Group contract rows by item and reject missing or duplicate conditions."""
    grouped: dict[str, dict[str, Mapping[str, Any]]] = {}
    rows = list(items)
    reject_draft_failures(rows)
    for item in rows:
        item_id = str(item.get("item_id", "<unknown>"))
        condition = item.get("condition")
        if condition not in CONDITIONS:
            continue
        by_condition = grouped.setdefault(item_id, {})
        if condition in by_condition:
            raise ValueError(
                f"item {item_id}: duplicate condition {condition}"
            )
        by_condition[str(condition)] = item
    for item_id, by_condition in grouped.items():
        missing = set(CONDITIONS) - set(by_condition)
        if missing:
            raise ValueError(
                f"item {item_id}: missing variant(s) {', '.join(sorted(missing))}"
            )
        reference = by_condition["RU-P"]
        reference_options = reference.get("options")
        reference_gold = reference.get("gold")
        reference_fields = _item_fields(reference, item_id)
        for condition in ("RU-R", "RU-X"):
            item = by_condition[condition]
            if item.get("gold") != reference_gold:
                raise ValueError(f"item {item_id}: gold differs in {condition}")
            fields = _item_fields(item, item_id)
            if len(fields) != len(reference_fields):
                raise ValueError(f"item {item_id}: option count differs in {condition}")
            if not isinstance(reference_options, list):
                raise ValueError(f"item {item_id}: options must be a list")
    if not grouped:
        raise ValueError("No RU-P, RU-R, and RU-X rows were provided")
    return grouped


def compute_edit_distance(
    items: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return one pooled field-distance summary for each required variant pair."""
    grouped = _group_items(items)
    summaries: list[dict[str, Any]] = []
    for left_condition, right_condition in PAIRS:
        raw_distances: list[int] = []
        normalized_distances: list[float] = []
        identical_fields = 0
        identical_items = 0
        for item_id, by_condition in grouped.items():
            left_fields = _item_fields(by_condition[left_condition], item_id)
            right_fields = _item_fields(by_condition[right_condition], item_id)
            if len(left_fields) != len(right_fields):
                raise ValueError(
                    f"item {item_id}: field count differs for "
                    f"{left_condition} vs {right_condition}"
                )
            item_identical = True
            for left, right in zip(left_fields, right_fields):
                distance = levenshtein_distance(left, right)
                raw_distances.append(distance)
                denominator = max(len(left), len(right))
                normalized_distances.append(
                    distance / denominator if denominator else 0.0
                )
                if left == right:
                    identical_fields += 1
                else:
                    item_identical = False
            identical_items += int(item_identical)
        field_count = len(raw_distances)
        item_count = len(grouped)
        summaries.append({
            "variant_pair": f"{left_condition} vs {right_condition}",
            "n_items": item_count,
            "n_fields": field_count,
            "mean_char_edit_distance": sum(raw_distances) / field_count,
            "mean_normalized_edit_distance": sum(normalized_distances) / field_count,
            "share_items_identical": identical_items / item_count,
            "share_fields_identical": identical_fields / field_count,
        })
    return summaries


def default_output_path() -> Path:
    """Return a temporary CSV path, never a project results path."""
    return Path(tempfile.gettempdir()) / "roman_urdu_edit_distance.csv"


def _reject_results_path(path: Path) -> None:
    resolved = path.resolve()
    results_dir = (ROOT / "results").resolve()
    try:
        resolved.relative_to(results_dir)
    except ValueError:
        return
    raise ValueError("edit-distance output must not be written under results/")


def write_edit_distance(
    items: Iterable[Mapping[str, Any]],
    output_path: Path | None = None,
) -> Path:
    """Write the three-row CSV and return its path."""
    target = Path(output_path) if output_path is not None else default_output_path()
    _reject_results_path(target)
    summaries = compute_edit_distance(items)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(summaries)
    return target


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    """Read contract rows and write edit-distance summaries."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("data/processed/items_v1.jsonl")
    )
    parser.add_argument("--out", type=Path, default=default_output_path())
    args = parser.parse_args()
    output = write_edit_distance(_read_jsonl(args.input), args.out)
    print(f"Edit-distance CSV saved to {output}")


if __name__ == "__main__":
    main()
