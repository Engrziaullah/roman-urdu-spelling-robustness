"""Run resumable, schema-checked evaluation requests from the repository root."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from src.eval.config import (
    ConfigError,
    ModelConfig,
    RunSettings,
    configured_model_slugs,
    load_model_config,
    load_run_settings,
)
from src.eval.parse import parse_answer
from src.eval.prompt import PromptTemplateError, build_prompt
from src.eval.providers import (
    MockProvider,
    Provider,
    ProviderError,
    create_provider,
)
from src.eval.runlog import append_result, append_run_summary, read_daily_call_count


ITEM_FIELDS = {
    "item_id",
    "source_row",
    "domain",
    "subject",
    "condition",
    "question",
    "options",
    "gold",
    "verified",
    "sample_rank",
    "notes",
}
CONDITIONS = {"NU", "RU-P", "RU-R", "RU-X", "RT"}


class RunInputError(ValueError):
    """Raised when an input file or run request violates the item contract."""


@dataclass(frozen=True)
class RunSummary:
    model_slug: str
    run_ids: tuple[str, ...]
    calls_made: int
    cache_hits: int
    errors: int
    processed_requests: int
    invalid_count: int
    invalid_rate: float
    latency_mean_s: float | None
    latency_min_s: float | None
    latency_max_s: float | None
    stopped_after_consecutive_failures: bool
    stopped_after_daily_quota: bool
    stopped_after_rate_limit: bool
    schema_problems: tuple[str, ...] = ()


class _RateLimiter:
    def __init__(
        self,
        requests_per_minute: int,
        sleep: Callable[[float], None],
        monotonic: Callable[[], float],
    ):
        self._interval = 60.0 / requests_per_minute
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request: float | None = None

    def wait(self) -> None:
        now = self._monotonic()
        if self._last_request is not None:
            delay = self._interval - (now - self._last_request)
            if delay > 0:
                self._sleep(delay)
        self._last_request = self._monotonic()


def _validate_item(row: Any, path: Path, line_number: int) -> dict[str, Any]:
    location = f"{path}:{line_number}"
    if not isinstance(row, dict):
        raise RunInputError(f"Expected a JSON object at {location}.")
    if set(row) != ITEM_FIELDS:
        raise RunInputError(
            f"Item schema mismatch at {location}; missing={sorted(ITEM_FIELDS - set(row))}, "
            f"extra={sorted(set(row) - ITEM_FIELDS)}."
        )
    text_fields = (
        "item_id",
        "source_row",
        "domain",
        "subject",
        "condition",
        "question",
        "gold",
        "notes",
    )
    for field_name in text_fields:
        if not isinstance(row[field_name], str):
            raise RunInputError(f"Field '{field_name}' must be text at {location}.")
    if not row["item_id"]:
        raise RunInputError(f"Field 'item_id' must be non-empty at {location}.")
    if not row["question"].strip():
        raise RunInputError(f"Field 'question' must be non-empty at {location}.")
    if row["condition"] not in CONDITIONS:
        raise RunInputError(f"Unsupported condition at {location}: {row['condition']!r}.")
    if not isinstance(row["options"], list) or not row["options"] or not all(
        isinstance(option, str) and option.strip() for option in row["options"]
    ):
        raise RunInputError(f"Field 'options' must be a non-empty text list at {location}.")
    if len(row["options"]) > 26:
        raise RunInputError(f"More than 26 options are unsupported at {location}.")
    expected_gold = chr(ord("A") + len(row["options"]) - 1)
    if (
        len(row["gold"]) != 1
        or row["gold"] < "A"
        or row["gold"] > expected_gold
    ):
        raise RunInputError(f"Field 'gold' is outside the option range at {location}.")
    if not isinstance(row["verified"], bool):
        raise RunInputError(f"Field 'verified' must be boolean at {location}.")
    if isinstance(row["sample_rank"], bool) or not isinstance(row["sample_rank"], int):
        raise RunInputError(f"Field 'sample_rank' must be an integer at {location}.")
    return row


def read_items(items_path: str | Path, *, mock: bool = False) -> list[dict[str, Any]]:
    """Read JSONL items and enforce the exact CONTRACTS section 1 field set."""
    path = Path(items_path)
    try:
        with path.open(encoding="utf-8") as file:
            lines = list(file)
    except OSError as exc:
        raise RunInputError(f"Cannot read items file {path}: {exc}") from exc
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RunInputError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
        row = _validate_item(parsed, path, line_number)
        key = (row["item_id"], row["condition"])
        if key in seen:
            raise RunInputError(
                f"Duplicate item_id/condition {key!r} in {path}:{line_number}."
            )
        seen.add(key)
        if mock and "mock" not in row["notes"].lower() and not row["item_id"].lower().startswith("mock"):
            raise RunInputError(
                f"Mock input must be clearly labelled in item_id or notes ({path}:{line_number})."
            )
        items.append(row)
    if not items:
        raise RunInputError(f"No items found in {path}.")
    return items


def _load_existing_keys(model_output_dir: Path) -> set[tuple[str, str, str, int]]:
    latest_rows: dict[
        tuple[str, str, str, int],
        tuple[tuple[int, int, str], bool],
    ] = {}
    if not model_output_dir.exists():
        return set()
    for result_file in sorted(model_output_dir.glob("*.jsonl")):
        try:
            file_order = result_file.stat().st_mtime_ns
            with result_file.open(encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise RunInputError(
                            f"Invalid cached JSON at {result_file}:{line_number}: {exc}"
                        ) from exc
                    if not isinstance(row, dict) or not all(
                        name in row
                        for name in (
                            "model_slug",
                            "item_id",
                            "condition",
                            "repeat",
                            "error",
                        )
                    ):
                        raise RunInputError(
                            f"Cached row lacks cache-key/error fields at "
                            f"{result_file}:{line_number}."
                        )
                    key = (
                        row["model_slug"],
                        row["item_id"],
                        row["condition"],
                        row["repeat"],
                    )
                    order = (file_order, line_number, str(result_file))
                    if key not in latest_rows or order > latest_rows[key][0]:
                        latest_rows[key] = (order, row["error"] is None)
        except OSError as exc:
            raise RunInputError(f"Cannot read cached results {result_file}: {exc}") from exc
    return {key for key, (_order, finished) in latest_rows.items() if finished}


def _normalized_items_sha256(items_path: str | Path) -> str:
    """Hash UTF-8 item text after normalizing CRLF newlines to LF."""
    path = Path(items_path)
    try:
        with path.open(encoding="utf-8", newline="") as file:
            normalized = file.read().replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as exc:
        raise RunInputError(f"Cannot hash UTF-8 items file {path}: {exc}") from exc
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _verify_frozen_items_hash(items_path: str | Path, marker_path: Path) -> None:
    """Require the marker's items_v1.jsonl SHA-256 to match the supplied items file."""
    actual = _normalized_items_sha256(items_path)
    if not marker_path.is_file():
        raise RunInputError(
            f"Non-NU real runs require {marker_path} with an "
            f"'items_v1.jsonl sha256: <64 hex chars>' line; "
            f"expected hash: <missing>, actual hash: {actual}."
        )
    try:
        marker_text = marker_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise RunInputError(f"Cannot read frozen marker {marker_path}: {exc}") from exc
    match = re.search(
        r"(?im)^\s*items_v1\.jsonl\s+sha256:\s*([0-9a-f]{64})\s*$",
        marker_text,
    )
    expected = match.group(1).lower() if match else "<missing>"
    if expected != actual:
        raise RunInputError(
            f"Frozen item hash mismatch in {marker_path}: "
            f"expected hash: {expected}, actual hash: {actual}."
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _date_text(run_date: str | None) -> str:
    if run_date is None:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        date.fromisoformat(run_date)
    except ValueError as exc:
        raise ValueError("run_date must use YYYY-MM-DD.") from exc
    return run_date


def _safe_purpose(purpose: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", purpose):
        raise ValueError("purpose may contain only letters, digits, '_' and '-'.")
    return purpose


def _ensure_mock_output_is_temporary(output_dir: Path, mock: bool) -> None:
    if not mock:
        return
    repo_root = Path(__file__).resolve().parents[2]
    protected = (repo_root / "results" / "raw").resolve()
    target = output_dir.resolve()
    if target == protected or protected in target.parents:
        raise ValueError("Mock output must use a temporary directory, never results/raw/.")
    if target == repo_root or repo_root in target.parents:
        raise ValueError("Mock output must be outside the repository.")
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target != temp_root and temp_root not in target.parents:
        raise ValueError(
            f"Mock output must be under the system temporary directory {temp_root}."
        )


def _select_items(
    items: list[dict[str, Any]],
    conditions: Sequence[str],
    max_items: int | None,
    item_ids: Sequence[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    item_order: list[str] = []
    by_condition: dict[str, dict[str, dict[str, Any]]] = {}
    for item in items:
        item_id = item["item_id"]
        if item_id not in item_order:
            item_order.append(item_id)
        by_condition.setdefault(item["condition"], {})[item_id] = item
    if item_ids is not None:
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("item_ids must not contain duplicates.")
        known_ids = set(item_order)
        unknown_ids = [item_id for item_id in item_ids if item_id not in known_ids]
        if unknown_ids:
            raise RunInputError(
                f"Requested item_id {unknown_ids[0]!r} is missing from the items file."
            )
        item_order = list(item_ids)
    if max_items is not None:
        if isinstance(max_items, bool) or max_items <= 0:
            raise ValueError("max_items must be a positive integer.")
        item_order = item_order[:max_items]
    selected: dict[str, list[dict[str, Any]]] = {}
    for condition in conditions:
        condition_items = by_condition.get(condition, {})
        missing = [item_id for item_id in item_order if item_id not in condition_items]
        if missing:
            raise RunInputError(
                f"Items file is missing condition {condition!r} for {len(missing)} "
                f"selected item(s), starting with {missing[0]!r}."
            )
        selected[condition] = [condition_items[item_id] for item_id in item_order]
    return selected


def run_pipeline(
    *,
    items_path: str | Path,
    model_config: ModelConfig,
    settings: RunSettings,
    provider: Provider,
    output_dir: str | Path,
    conditions: Sequence[str] = ("NU",),
    repeats: int = 1,
    purpose: str = "nu",
    max_items: int | None = None,
    mock: bool = False,
    frozen_marker: str | Path | None = None,
    run_log_path: str | Path | None = None,
    run_date: str | None = None,
    item_ids: Sequence[str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> RunSummary:
    """Run selected conditions with retries, cache, schema logging, and rate limits."""
    if not conditions:
        raise ValueError("At least one condition is required.")
    if len(set(conditions)) != len(conditions):
        raise ValueError("Conditions must not be repeated.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", model_config.slug):
        raise ValueError("model_slug must contain only lowercase letters, digits, '.', '_' or '-'.")
    unknown = set(conditions) - CONDITIONS
    if unknown:
        raise ValueError(f"Unsupported condition(s): {sorted(unknown)}.")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer.")
    purpose = _safe_purpose(purpose)
    run_date_text = _date_text(run_date)
    output_path = Path(output_dir)
    _ensure_mock_output_is_temporary(output_path, mock)
    if not mock and run_log_path is None:
        raise ValueError("run_log_path is required for every real run.")

    if not mock and any(condition != "NU" for condition in conditions):
        marker = (
            Path(frozen_marker)
            if frozen_marker is not None
            else Path(__file__).resolve().parents[2]
            / "data"
            / "processed"
            / "FROZEN.md"
        )
        _verify_frozen_items_hash(items_path, marker)

    items = read_items(items_path, mock=mock)
    selected = _select_items(items, conditions, max_items, item_ids)
    calls_made = 0
    cache_hits = 0
    errors = 0
    processed_requests = 0
    invalid_count = 0
    latencies: list[float] = []
    run_ids: list[str] = []
    model_output_dir = output_path / model_config.slug
    cached = _load_existing_keys(model_output_dir)
    consecutive_failures = 0
    limiter = _RateLimiter(
        model_config.requests_per_minute,
        sleep=sleep,
        monotonic=monotonic,
    )
    stop_after_failures = False
    stop_after_daily_quota = False
    stop_after_rate_limit = False
    daily_calls_made = (
        read_daily_call_count(run_log_path, model_config.slug, run_date_text)
        if not mock and run_log_path is not None
        else 0
    )

    for repeat in range(1, repeats + 1):
        run_id = f"{run_date_text}_{purpose}_r{repeat}"
        run_ids.append(run_id)
        run_calls = 0
        run_cache_hits = 0
        run_errors = 0
        run_processed = 0
        run_invalid = 0
        run_latencies: list[float] = []
        for condition in conditions:
            for item in selected[condition]:
                cache_key = (model_config.slug, item["item_id"], condition, repeat)
                if cache_key in cached:
                    cache_hits += 1
                    run_cache_hits += 1
                    continue
                if not mock and daily_calls_made >= model_config.requests_per_day:
                    stop_after_daily_quota = True
                    break
                prompt, prompt_hash = build_prompt(
                    item, condition, settings.paths["prompt_template"]
                )
                raw_output = ""
                parsed_answer: str | None = None
                valid = False
                error: str | None = None
                latency_s = 0.0
                attempt = 0
                attempted = False
                while True:
                    if not mock and daily_calls_made >= model_config.requests_per_day:
                        stop_after_daily_quota = True
                        break
                    if not mock:
                        limiter.wait()
                    started = time.perf_counter()
                    attempted = True
                    calls_made += 1
                    run_calls += 1
                    if not mock:
                        daily_calls_made += 1
                    try:
                        raw_output, provider_latency, _returned_model = provider.complete(
                            prompt, model_config, settings
                        )
                        latency_s = max(0.0, float(provider_latency))
                        if not isinstance(raw_output, str):
                            raise ProviderError(
                                "Provider returned non-text output.", retryable=False
                            )
                        parsed_answer, valid = parse_answer(
                            raw_output, [chr(ord("A") + index) for index in range(len(item["options"]))]
                        )
                        error = None
                        break
                    except ProviderError as exc:
                        latency_s = max(0.0, time.perf_counter() - started)
                        if exc.retryable and attempt < settings.max_retries:
                            if exc.status_code == 429:
                                error = str(exc)
                                stop_after_rate_limit = True
                                break
                            error = str(exc)
                            sleep(settings.backoff_initial_s * (2**attempt))
                            attempt += 1
                            continue
                        error = str(exc)
                        if exc.status_code == 429:
                            stop_after_rate_limit = True
                        break

                if not attempted:
                    break
                row = {
                    "run_id": run_id,
                    "model_slug": model_config.slug,
                    "model_string": model_config.model_string,
                    "provider": model_config.provider,
                    "date_utc": _utc_now(),
                    "item_id": item["item_id"],
                    "condition": condition,
                    "repeat": repeat,
                    "prompt_hash": prompt_hash,
                    "raw_output": raw_output,
                    "parsed_answer": parsed_answer,
                    "valid": valid,
                    "latency_s": latency_s,
                    "error": error,
                }
                append_result(output_path, model_config.slug, run_id, row)
                cached.add(cache_key)
                processed_requests += 1
                run_processed += 1
                latencies.append(latency_s)
                run_latencies.append(latency_s)
                if not valid:
                    invalid_count += 1
                    run_invalid += 1
                if error is not None:
                    errors += 1
                    run_errors += 1
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0
                if consecutive_failures >= settings.max_consecutive_failures:
                    stop_after_failures = True
                    break
                if stop_after_daily_quota or stop_after_rate_limit:
                    break
            if stop_after_failures:
                break
            if stop_after_daily_quota or stop_after_rate_limit:
                break

        if not mock and run_log_path is not None:
            stop_reason = (
                "rate_limit"
                if stop_after_rate_limit
                else "daily_quota"
                if stop_after_daily_quota
                else "consecutive_failures"
                if stop_after_failures
                else "complete"
            )
            append_run_summary(
                run_log_path,
                date_utc=_utc_now(),
                run_id=run_id,
                model_slug=model_config.slug,
                model_string=model_config.model_string,
                calls_made=run_calls,
                cache_hits=run_cache_hits,
                errors=run_errors,
                invalid_rate=run_invalid / run_processed if run_processed else 0.0,
                latency_mean_s=(
                    sum(run_latencies) / len(run_latencies) if run_latencies else None
                ),
                latency_min_s=min(run_latencies) if run_latencies else None,
                latency_max_s=max(run_latencies) if run_latencies else None,
                stop_reason=stop_reason,
            )
        if stop_after_failures or stop_after_daily_quota or stop_after_rate_limit:
            break

    return RunSummary(
        model_slug=model_config.slug,
        run_ids=tuple(run_ids),
        calls_made=calls_made,
        cache_hits=cache_hits,
        errors=errors,
        processed_requests=processed_requests,
        invalid_count=invalid_count,
        invalid_rate=invalid_count / processed_requests if processed_requests else 0.0,
        latency_mean_s=sum(latencies) / len(latencies) if latencies else None,
        latency_min_s=min(latencies) if latencies else None,
        latency_max_s=max(latencies) if latencies else None,
        stopped_after_consecutive_failures=stop_after_failures,
        stopped_after_daily_quota=stop_after_daily_quota,
        stopped_after_rate_limit=stop_after_rate_limit,
    )


def _mock_settings(repo_root: Path) -> RunSettings:
    """Settings for a no-network mock run; independent of unapproved G0 values."""
    return RunSettings(
        seed=0,
        max_output_tokens=1,
        temperature=0.0,
        request_timeout_s=1.0,
        max_retries=0,
        max_consecutive_failures=5,
        backoff_initial_s=0.0,
        paths={
            "results_raw": repo_root / "results" / "raw",
            "run_log": repo_root / "results" / "RUN_LOG.md",
            "prompt_template": repo_root / "tests" / "fixtures" / "mock_prompt.txt",
        },
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-slug", required=True)
    parser.add_argument("--items", required=True, help="CONTRACTS item JSONL path")
    parser.add_argument("--conditions", default="NU", help="Comma-separated conditions")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--purpose")
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument(
        "--noise-subset",
        action="store_true",
        help="Use configured noise-subset item IDs and repeat count.",
    )
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", help="Output root; required for --mock")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; mock runs never write to results/raw or RUN_LOG.md."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    conditions = tuple(part.strip() for part in args.conditions.split(",") if part.strip())
    if not conditions:
        parser.error("--conditions must include at least one condition.")
    if len(set(conditions)) != len(conditions):
        parser.error("--conditions must not repeat a condition.")
    if set(conditions) - CONDITIONS:
        parser.error(f"Unsupported condition(s): {sorted(set(conditions) - CONDITIONS)}.")
    if args.repeats < 1:
        parser.error("--repeats must be a positive integer.")
    try:
        item_ids: Sequence[str] | None = None
        purpose = args.purpose or ("noise" if args.noise_subset else "nu")
        repeats = args.repeats
        if args.noise_subset and args.max_items is not None:
            parser.error("--max-items cannot be combined with --noise-subset.")

        if args.mock:
            if not args.output_dir:
                parser.error("--output-dir is required with --mock; use a temporary directory.")
            settings = _mock_settings(repo_root)
            model_config = ModelConfig(
                slug=args.model_slug,
                provider="mock",
                model_string="mock",
                api_key_env="",
                requests_per_minute=60,
                requests_per_day=60,
                checked_on="mock",
            )
            provider: Provider | None = MockProvider()
            mock = True
        else:
            settings = load_run_settings(args.config)
            models_path = Path(args.models)
            if args.dry_run:
                if args.model_slug not in configured_model_slugs(models_path):
                    raise ConfigError(
                        f"Unknown model slug '{args.model_slug}' in {models_path}."
                    )
                model_config = None
                provider = None
            else:
                model_config = load_model_config(
                    models_path,
                    args.model_slug,
                )
                provider = create_provider(model_config.provider)
            mock = False

        if args.noise_subset:
            if args.mock:
                configured_settings = load_run_settings(args.config)
                settings = replace(
                    configured_settings,
                    paths={
                        **configured_settings.paths,
                        "prompt_template": (
                            repo_root / "tests" / "fixtures" / "mock_prompt.txt"
                        ),
                    },
                )
            noise_subset = settings.noise_subset
            if noise_subset is None or len(noise_subset.item_ids) != noise_subset.n_items:
                raise ConfigError(
                    "A complete noise_subset block is required in configs/config.yaml."
                )
            item_ids = noise_subset.item_ids
            repeats = noise_subset.repeats

        if args.dry_run:
            items = read_items(args.items, mock=args.mock)
            selected = _select_items(items, conditions, args.max_items, item_ids)
            request_count = sum(len(rows) for rows in selected.values()) * repeats
            print(
                json.dumps(
                    {
                        "model_slug": args.model_slug,
                        "conditions": list(conditions),
                        "requests_planned": request_count,
                        "repeats": repeats,
                        "mock": args.mock,
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        output_dir = Path(args.output_dir) if args.output_dir else settings.paths["results_raw"]
        if model_config is None or provider is None:
            raise ConfigError("A model configuration and provider are required to run.")
        summary = run_pipeline(
            items_path=args.items,
            model_config=model_config,
            settings=settings,
            provider=provider,
            output_dir=output_dir,
            conditions=conditions,
            repeats=repeats,
            purpose=purpose,
            max_items=args.max_items,
            mock=mock,
            run_log_path=settings.paths["run_log"],
            item_ids=item_ids,
        )
        print(json.dumps(asdict(summary), ensure_ascii=False))
        return 0
    except (ConfigError, RunInputError, PromptTemplateError, ProviderError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
