"""Create a deterministic, domain-stratified item list for noise repeats."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Sequence

import yaml

from src.eval.run import read_items


class NoiseSubsetError(ValueError):
    """Raised when the item sample or noise-subset configuration is invalid."""


def choose_noise_ids(
    items_path: str | Path,
    *,
    seed: int,
    n_per_domain: int = 6,
) -> list[str]:
    """Select an equal number of core item IDs from every observed domain."""
    items = read_items(items_path)
    core_by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        if item["condition"] == "NU" and item["sample_rank"] <= 200:
            core_by_id[item["item_id"]] = item
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for item in core_by_id.values():
        by_domain.setdefault(item["domain"], []).append(item)
    if len(by_domain) != 5:
        raise NoiseSubsetError(
            f"Expected exactly five domains in the core; found {len(by_domain)}."
        )
    insufficient = [
        domain for domain, group in by_domain.items() if len(group) < n_per_domain
    ]
    if insufficient:
        raise NoiseSubsetError(
            f"Not enough core items for {n_per_domain} per domain: "
            f"{', '.join(sorted(insufficient))}."
        )

    generator = random.Random(seed)
    selected = [
        item
        for domain in sorted(by_domain)
        for item in generator.sample(
            sorted(by_domain[domain], key=lambda row: row["sample_rank"]),
            n_per_domain,
        )
    ]
    selected.sort(key=lambda row: row["sample_rank"])
    return [item["item_id"] for item in selected]


def _read_config(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except OSError as exc:
        raise NoiseSubsetError(f"Cannot read configuration {config_path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise NoiseSubsetError(f"Invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise NoiseSubsetError(f"Configuration in {config_path} must be a mapping.")
    seed = data.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise NoiseSubsetError(f"Configuration seed must be an integer in {config_path}.")
    return data


def _update_config(
    config_path: Path,
    *,
    seed: int,
    item_ids: list[str],
    n_items: int,
    repeats: int,
    force: bool,
) -> None:
    text = config_path.read_text(encoding="utf-8")
    data = _read_config(config_path)
    existing = data.get("noise_subset")
    if isinstance(existing, dict) and existing.get("item_ids") and not force:
        raise NoiseSubsetError(
            "configs/config.yaml already contains non-empty noise_subset.item_ids; "
            "use --force to replace them."
        )
    block = yaml.safe_dump(
        {
            "noise_subset": {
                "n_items": n_items,
                "repeats": repeats,
                "item_ids": item_ids,
            }
        },
        allow_unicode=True,
        sort_keys=False,
    )
    marker = re.search(r"(?m)^noise_subset\s*:\s*(?:\r?\n|$)", text)
    if marker is None:
        updated = text.rstrip() + "\n\n" + block
    else:
        following_root = re.search(r"(?m)^(?=\S)(?!#)", text[marker.end() :])
        block_end = (
            marker.end() + following_root.start()
            if following_root is not None
            else len(text)
        )
        updated = text[: marker.start()] + block + text[block_end:]
    try:
        with config_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(updated)
    except OSError as exc:
        raise NoiseSubsetError(f"Cannot write configuration {config_path}: {exc}") from exc
    validated = _read_config(config_path)
    if validated.get("seed") != seed:
        raise NoiseSubsetError("Configuration seed changed unexpectedly while updating it.")


def create_noise_subset(
    items_path: str | Path,
    config_path: str | Path,
    *,
    force: bool = False,
) -> list[str]:
    """Select noise IDs from the configured seed and persist them exactly once."""
    config_file = Path(config_path)
    data = _read_config(config_file)
    item_ids = choose_noise_ids(items_path, seed=data["seed"])
    _update_config(
        config_file,
        seed=data["seed"],
        item_ids=item_ids,
        n_items=len(item_ids),
        repeats=3,
        force=force,
    )
    return item_ids


def main(argv: Sequence[str] | None = None) -> int:
    """Write the selected IDs to the given config and print them as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", default="data/processed/items_nu.jsonl")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        item_ids = create_noise_subset(args.items, args.config, force=args.force)
    except (OSError, NoiseSubsetError) as exc:
        parser.error(str(exc))
    print(json.dumps({"n_items": len(item_ids), "item_ids": item_ids}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
