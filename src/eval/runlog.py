"""Append contract-shaped result rows and concise real-run summaries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


RESULT_FIELDS = (
    "run_id",
    "model_slug",
    "model_string",
    "provider",
    "date_utc",
    "item_id",
    "condition",
    "repeat",
    "prompt_hash",
    "raw_output",
    "parsed_answer",
    "valid",
    "latency_s",
    "error",
)


def _safe_slug(model_slug: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", model_slug):
        raise ValueError("model_slug must contain only lowercase letters, digits, '.', '_' or '-'.")
    return model_slug


def append_result(
    output_root: str | Path,
    model_slug: str,
    run_id: str,
    row: Mapping[str, Any],
) -> Path:
    """Append exactly one CONTRACTS section 2 row without overwriting prior rows."""
    expected = set(RESULT_FIELDS)
    actual = set(row)
    if actual != expected:
        raise ValueError(
            f"Result row fields mismatch; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}."
        )
    if row["model_slug"] != model_slug or row["run_id"] != run_id:
        raise ValueError("Result row model_slug/run_id must match its output path.")
    if not isinstance(row["valid"], bool):
        raise ValueError("Result row 'valid' must be boolean.")
    latency = row["latency_s"]
    if isinstance(latency, bool) or not isinstance(latency, (int, float)) or latency < 0:
        raise ValueError("Result row 'latency_s' must be a non-negative number.")
    if not isinstance(row["error"], (str, type(None))):
        raise ValueError("Result row 'error' must be text or null.")

    directory = Path(output_root) / _safe_slug(model_slug)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id}.jsonl"
    serialized = json.dumps(dict(row), ensure_ascii=False, allow_nan=False)
    with path.open("a", encoding="utf-8", newline="\n") as file:
        file.write(serialized + "\n")
    return path


def append_run_summary(
    path: str | Path,
    *,
    date_utc: str,
    run_id: str,
    model_slug: str,
    model_string: str,
    calls_made: int,
    cache_hits: int,
    errors: int,
    invalid_rate: float,
    latency_mean_s: float | None,
    latency_min_s: float | None,
    latency_max_s: float | None,
) -> None:
    """Append a Markdown summary for a real run."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text("# Run log\n\n", encoding="utf-8")
    mean = "n/a" if latency_mean_s is None else f"{latency_mean_s:.4f}"
    minimum = "n/a" if latency_min_s is None else f"{latency_min_s:.4f}"
    maximum = "n/a" if latency_max_s is None else f"{latency_max_s:.4f}"
    line = (
        f"- {date_utc} | `{run_id}` | `{model_slug}` (`{model_string}`): "
        f"calls={calls_made}, cache_hits={cache_hits}, errors={errors}, "
        f"invalid_rate={invalid_rate:.4f}, latency_s mean/min/max="
        f"{mean}/{minimum}/{maximum}\n"
    )
    with output.open("a", encoding="utf-8", newline="\n") as file:
        file.write(line)
