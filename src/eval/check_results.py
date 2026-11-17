"""Check saved evaluation JSONL files against the result contract and run plan."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import yaml

from src.eval.run import read_items
from src.eval.runlog import RESULT_FIELDS


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except OSError as exc:
        raise ValueError(f"Cannot read YAML file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"YAML file {path} must contain a mapping.")
    return data


def check_results(
    results_dir: str | Path,
    items_path: str | Path,
    models_path: str | Path,
    config_path: str | Path,
    *,
    invalid_rate_threshold: float = 0.05,
) -> dict[str, Any]:
    """Return counts, missing/duplicate keys, validation findings, and dates."""
    if not 0 <= invalid_rate_threshold <= 1:
        raise ValueError("invalid_rate_threshold must be between 0 and 1.")
    items = read_items(items_path)
    item_map = {
        (item["item_id"], item["condition"]): item
        for item in items
    }
    conditions = sorted({item["condition"] for item in items})

    models_data = _read_yaml(Path(models_path))
    model_entries = models_data.get("evaluated_models")
    if not isinstance(model_entries, list):
        raise ValueError(f"Field 'evaluated_models' must be a list in {models_path}.")
    model_slugs = {
        model["slug"]
        for model in model_entries
        if isinstance(model, dict) and isinstance(model.get("slug"), str)
    }
    config_data = _read_yaml(Path(config_path))
    noise = config_data.get("noise_subset")
    noise_ids: set[str] = set()
    noise_repeats = 1
    if noise is not None:
        if not isinstance(noise, dict):
            raise ValueError(f"Field 'noise_subset' must be a mapping in {config_path}.")
        raw_ids = noise.get("item_ids", [])
        raw_repeats = noise.get("repeats", 1)
        if not isinstance(raw_ids, list) or not all(
            isinstance(item_id, str) for item_id in raw_ids
        ):
            raise ValueError(f"Field 'noise_subset.item_ids' is invalid in {config_path}.")
        if isinstance(raw_repeats, bool) or not isinstance(raw_repeats, int) or raw_repeats < 1:
            raise ValueError(f"Field 'noise_subset.repeats' is invalid in {config_path}.")
        noise_ids = set(raw_ids)
        noise_repeats = raw_repeats
        unknown_noise_ids = noise_ids - {item_id for item_id, _ in item_map}
        if unknown_noise_ids:
            raise ValueError(
                f"Noise subset contains unknown item IDs: {sorted(unknown_noise_ids)}."
            )

    root = Path(results_dir)
    problems: list[str] = []
    rows_by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    key_counts: Counter[tuple[str, str, str, int]] = Counter()
    model_strings: dict[str, set[str]] = defaultdict(set)
    observed_dates: dict[tuple[str, str], list[str]] = defaultdict(list)

    if root.exists():
        result_files = sorted(root.rglob("*.jsonl"))
    else:
        result_files = []
    for result_file in result_files:
        try:
            content = result_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            problems.append(f"Cannot read result file {result_file}: {exc}")
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            location = f"{result_file}:{line_number}"
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"Invalid JSON at {location}: {exc}")
                continue
            if not isinstance(row, dict):
                problems.append(f"Result row must be an object at {location}.")
                continue
            if set(row) != set(RESULT_FIELDS):
                missing_fields = sorted(set(RESULT_FIELDS) - set(row))
                extra_fields = sorted(set(row) - set(RESULT_FIELDS))
                problems.append(
                    f"Result field mismatch at {location}: "
                    f"missing={missing_fields}, extra={extra_fields}."
                )
            text_fields = (
                "run_id",
                "model_slug",
                "model_string",
                "provider",
                "date_utc",
                "item_id",
                "condition",
                "prompt_hash",
                "raw_output",
            )
            for field_name in text_fields:
                if not isinstance(row.get(field_name), str):
                    problems.append(f"{field_name} must be text at {location}.")
            repeat_value = row.get("repeat")
            if (
                isinstance(repeat_value, bool)
                or not isinstance(repeat_value, int)
                or repeat_value < 1
            ):
                problems.append(f"repeat must be a positive integer at {location}.")
            latency = row.get("latency_s")
            if (
                isinstance(latency, bool)
                or not isinstance(latency, (int, float))
                or latency < 0
            ):
                problems.append(f"latency_s must be non-negative at {location}.")
            if row.get("parsed_answer") is not None and not isinstance(
                row.get("parsed_answer"), str
            ):
                problems.append(f"parsed_answer must be text or null at {location}.")
            model_slug = row.get("model_slug")
            item_id = row.get("item_id")
            condition = row.get("condition")
            repeat = row.get("repeat")
            if not (
                isinstance(model_slug, str)
                and isinstance(item_id, str)
                and isinstance(condition, str)
                and isinstance(repeat, int)
                and not isinstance(repeat, bool)
            ):
                continue

            model_slugs.add(model_slug)
            rows_by_group[(model_slug, condition)].append(row)
            key = (model_slug, item_id, condition, repeat)
            key_counts[key] += 1
            if isinstance(row.get("model_string"), str):
                model_strings[model_slug].add(row["model_string"])
            date_text = row.get("date_utc")
            if isinstance(date_text, str):
                try:
                    parsed_date = datetime.fromisoformat(date_text.replace("Z", "+00:00"))
                except ValueError:
                    problems.append(f"Invalid date_utc at {location}: {date_text!r}.")
                else:
                    if parsed_date.utcoffset() is None or parsed_date.utcoffset().total_seconds() != 0:
                        problems.append(f"date_utc must be UTC at {location}.")
                    else:
                        observed_dates[(model_slug, condition)].append(date_text)

            item = item_map.get((item_id, condition))
            if item is None:
                problems.append(
                    f"Result key {(item_id, condition)!r} is absent from the items file "
                    f"at {location}."
                )
            option_count = len(item["options"]) if item is not None else 5
            allowed = {chr(ord("A") + index) for index in range(option_count)}
            parsed = row.get("parsed_answer")
            valid = row.get("valid")
            if parsed is not None and (not isinstance(parsed, str) or parsed not in allowed):
                problems.append(
                    f"parsed_answer is outside {sorted(allowed)} at {location}."
                )
            if not isinstance(valid, bool):
                problems.append(f"valid must be a boolean at {location}.")
            elif valid != (parsed is not None and parsed in allowed):
                problems.append(
                    f"valid is inconsistent with parsed_answer at {location}."
                )
            if not isinstance(row.get("error"), (str, type(None))):
                problems.append(f"error must be text or null at {location}.")

    duplicates = sorted(key for key, count in key_counts.items() if count > 1)
    for key in duplicates:
        problems.append(f"Duplicate result key: {key!r}.")

    expected_keys: set[tuple[str, str, str, int]] = set()
    for model_slug in model_slugs:
        for item_id, condition in item_map:
            repeat_count = noise_repeats if item_id in noise_ids else 1
            expected_keys.update(
                (model_slug, item_id, condition, repeat)
                for repeat in range(1, repeat_count + 1)
            )
    existing_keys = set(key_counts)
    missing_keys = sorted(expected_keys - existing_keys)
    if missing_keys:
        problems.append(f"{len(missing_keys)} expected result combination(s) are missing.")
    unexpected_keys = sorted(existing_keys - expected_keys)
    if unexpected_keys:
        problems.append(f"{len(unexpected_keys)} unexpected result combination(s) were found.")

    for model_slug, values in sorted(model_strings.items()):
        if len(values) > 1:
            problems.append(
                f"Model {model_slug!r} has multiple model_string values: {sorted(values)}."
            )

    model_reports: dict[str, Any] = {}
    for model_slug in sorted(model_slugs):
        condition_reports: dict[str, Any] = {}
        for condition in conditions:
            group = rows_by_group.get((model_slug, condition), [])
            valid_rows = sum(row.get("valid") is True for row in group)
            invalid_rate = (len(group) - valid_rows) / len(group) if group else 0.0
            error_rows = sum(row.get("error") is not None for row in group)
            missing = [
                key for key in missing_keys
                if key[0] == model_slug and key[2] == condition
            ]
            duplicate_group = [
                key for key in duplicates
                if key[0] == model_slug and key[2] == condition
            ]
            dates = observed_dates.get((model_slug, condition), [])
            condition_reports[condition] = {
                "rows": len(group),
                "valid_rows": valid_rows,
                "invalid_rate": invalid_rate,
                "error_rows": error_rows,
                "missing": [list(key[1:]) for key in missing],
                "duplicate_keys": [list(key[1:]) for key in duplicate_group],
                "date_range": [min(dates), max(dates)] if dates else None,
            }
            if invalid_rate > invalid_rate_threshold:
                problems.append(
                    f"Invalid rate for {model_slug}/{condition} is "
                    f"{invalid_rate:.4f}, above {invalid_rate_threshold:.4f}."
                )
            if error_rows:
                problems.append(f"{error_rows} error row(s) for {model_slug}/{condition}.")
        model_reports[model_slug] = {
            "model_strings": sorted(model_strings.get(model_slug, set())),
            "multiple_model_strings": len(model_strings.get(model_slug, set())) > 1,
            "conditions": condition_reports,
        }

    return {
        "models": model_reports,
        "duplicate_keys": [list(key) for key in duplicates],
        "problems": problems,
        "ok": not problems,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Print a read-only JSON report and return nonzero when it finds a problem."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/raw")
    parser.add_argument("--items", default="data/processed/items_v1.jsonl")
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--invalid-rate-threshold", type=float, default=0.05)
    args = parser.parse_args(argv)
    try:
        report = check_results(
            args.results_dir,
            args.items,
            args.models,
            args.config,
            invalid_rate_threshold=args.invalid_rate_threshold,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
