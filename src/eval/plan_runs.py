"""Estimate evaluation request counts and provider-limited run duration."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml

from src.eval.run import read_items


CONDITIONS = {"NU", "RU-P", "RU-R", "RU-X", "RT"}


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


def _limit(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def plan_run_counts(
    items_path: str | Path,
    models_path: str | Path,
    config_path: str | Path,
    *,
    requested_conditions: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Return full-pass, noise, and estimated days for every configured model."""
    items = read_items(items_path)
    item_ids = {item["item_id"] for item in items}
    observed_conditions = {item["condition"] for item in items}
    conditions = set(requested_conditions or observed_conditions)
    if not conditions:
        raise ValueError("No conditions were selected for planning.")
    if conditions - CONDITIONS:
        raise ValueError(f"Unsupported conditions: {sorted(conditions - CONDITIONS)}.")
    full_pass = len(item_ids) * len(conditions)

    models_data = _read_yaml(Path(models_path))
    models = models_data.get("evaluated_models")
    if not isinstance(models, list):
        raise ValueError(f"Field 'evaluated_models' must be a list in {models_path}.")
    run_config = _read_yaml(Path(config_path))
    noise = run_config.get("noise_subset")
    if noise is None:
        noise_items = 0
        noise_repeats = 1
    elif isinstance(noise, dict):
        raw_n = noise.get("n_items", 0)
        raw_repeats = noise.get("repeats", 1)
        noise_items = raw_n if isinstance(raw_n, int) and not isinstance(raw_n, bool) else 0
        noise_repeats = (
            raw_repeats
            if isinstance(raw_repeats, int) and not isinstance(raw_repeats, bool)
            else 1
        )
    else:
        raise ValueError(f"Field 'noise_subset' must be a mapping in {config_path}.")
    noise_extra = noise_items * len(conditions) * max(0, noise_repeats - 1)

    plans: list[dict[str, Any]] = []
    for model in models:
        if not isinstance(model, dict) or not isinstance(model.get("slug"), str):
            raise ValueError(f"Every model entry in {models_path} must have a slug.")
        rpm = _limit(model.get("requests_per_minute"))
        rpd = _limit(model.get("requests_per_day"))
        capacity = min(rpd, rpm * 1440) if rpm is not None and rpd is not None else None
        total_requests = full_pass + noise_extra
        days = (
            math.ceil(total_requests / capacity)
            if capacity is not None and capacity > 0
            else None
        )
        plans.append(
            {
                "model_slug": model["slug"],
                "requests_per_minute": rpm if rpm is not None else "unknown",
                "requests_per_day": rpd if rpd is not None else "unknown",
                "full_pass_requests": full_pass,
                "noise_extra_requests": noise_extra,
                "days": days if days is not None else "unknown",
            }
        )
    return plans


def main(argv: Sequence[str] | None = None) -> int:
    """Print a per-model request and time estimate without contacting providers."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/processed/items_nu.jsonl")
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument(
        "--conditions",
        help="Comma-separated conditions; defaults to those present in the items file.",
    )
    args = parser.parse_args(argv)
    conditions = (
        tuple(part.strip() for part in args.conditions.split(",") if part.strip())
        if args.conditions
        else None
    )
    try:
        plans = plan_run_counts(
            args.items,
            args.models,
            args.config,
            requested_conditions=conditions,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(
        "model_slug | requests_per_minute | requests_per_day | "
        "full_pass_requests | noise_extra_requests | days"
    )
    for plan in plans:
        print(
            f"{plan['model_slug']} | {plan['requests_per_minute']} | "
            f"{plan['requests_per_day']} | {plan['full_pass_requests']} | "
            f"{plan['noise_extra_requests']} | {plan['days']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
