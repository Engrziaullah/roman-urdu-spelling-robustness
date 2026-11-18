from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
import yaml

from src.eval.config import load_run_settings
from src.eval.make_noise_subset import NoiseSubsetError, choose_noise_ids, create_noise_subset
from src.eval.plan_runs import plan_run_counts
from src.eval.run import main


CONDITIONS = ("NU", "RU-P", "RU-R", "RU-X", "RT")
DOMAINS = ("Humanities", "Other", "Profession", "STEM", "Social Sciences")


def _item(item_id: str, rank: int, condition: str, options: int = 4) -> dict:
    labels = [chr(ord("A") + index) for index in range(options)]
    return {
        "item_id": item_id,
        "source_row": f"mock-{rank}",
        "domain": DOMAINS[(rank - 1) % len(DOMAINS)],
        "subject": "mock subject",
        "condition": condition,
        "question": "MOCK Urdu سوال",
        "options": [f"اختیار {label}" for label in labels],
        "gold": labels[-1],
        "verified": True,
        "sample_rank": rank,
        "notes": "MOCK synthetic item",
    }


def _write_items(path: Path, count: int, conditions: tuple[str, ...]) -> Path:
    rows = [
        _item(
            f"mock-item-{rank:03}",
            rank,
            condition,
            options=5 if rank == count else 4,
        )
        for rank in range(1, count + 1)
        for condition in conditions
    ]
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _config_data(tmp_path: Path, noise_subset: dict | None = None) -> dict:
    config = {
        "seed": 42,
        "max_output_tokens": 16,
        "temperature": 0,
        "request_timeout_s": 2,
        "max_retries": 0,
        "max_consecutive_failures": 5,
        "backoff_initial_s": 0,
        "paths": {
            "results_raw": str(tmp_path / "results" / "raw"),
            "run_log": str(tmp_path / "results" / "RUN_LOG.md"),
            "prompt_template": str(
                Path(__file__).resolve().parents[2]
                / "tests"
                / "fixtures"
                / "mock_prompt.txt"
            ),
        },
    }
    if noise_subset is not None:
        config["noise_subset"] = noise_subset
    return config


def test_noise_subset_is_seeded_stratified_and_protected_from_overwrite(
    tmp_path: Path,
) -> None:
    items_path = _write_items(tmp_path / "items.jsonl", 200, ("NU",))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "# Preserve existing config notes\n"
        + yaml.safe_dump(_config_data(tmp_path), sort_keys=False),
        encoding="utf-8",
    )

    selected = choose_noise_ids(items_path, seed=42)
    assert selected == choose_noise_ids(items_path, seed=42)
    written = create_noise_subset(items_path, config_path)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    rows = {
        row["item_id"]: row
        for row in (
            json.loads(line)
            for line in items_path.read_text(encoding="utf-8").splitlines()
        )
    }

    assert written == selected
    assert len(selected) == 30
    assert all(rows[item_id]["sample_rank"] <= 200 for item_id in selected)
    assert Counter(rows[item_id]["domain"] for item_id in selected) == {
        domain: 6 for domain in DOMAINS
    }
    assert config["noise_subset"]["n_items"] == 30
    assert config["noise_subset"]["repeats"] == 3
    assert "# Preserve existing config notes" in config_path.read_text(encoding="utf-8")
    assert load_run_settings(config_path).noise_subset.item_ids == tuple(selected)

    with pytest.raises(NoiseSubsetError, match="--force"):
        create_noise_subset(items_path, config_path)
    assert create_noise_subset(items_path, config_path, force=True) == selected


def test_noise_subset_cli_uses_configured_ids_and_three_repeats(
    tmp_path: Path,
) -> None:
    items_path = _write_items(tmp_path / "items.jsonl", 2, ("NU",))
    selected_id = "mock-item-001"
    config_path = tmp_path / "configs" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text(
        yaml.safe_dump(
            _config_data(
                tmp_path,
                {
                    "n_items": 1,
                    "repeats": 3,
                    "item_ids": [selected_id],
                },
            ),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "cli-output"

    result = main(
        [
            "--model-slug",
            "fixture",
            "--items",
            str(items_path),
            "--conditions",
            "NU",
            "--noise-subset",
            "--mock",
            "--output-dir",
            str(output_dir),
            "--config",
            str(config_path),
        ]
    )

    assert result == 0
    rows = [
        json.loads(result_line)
        for result_file in (output_dir / "fixture").glob("*.jsonl")
        for result_line in result_file.read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 3
    assert {row["item_id"] for row in rows} == {selected_id}
    assert {row["repeat"] for row in rows} == {1, 2, 3}


def test_run_planner_reports_unknown_todos_and_rate_limited_days(
    tmp_path: Path,
) -> None:
    items_path = _write_items(tmp_path / "items.jsonl", 2, ("NU",))
    models_path = tmp_path / "models.yaml"
    models_path.write_text(
        yaml.safe_dump(
            {
                "evaluated_models": [
                    {
                        "slug": "known",
                        "requests_per_minute": 1,
                        "requests_per_day": 100,
                    },
                    {
                        "slug": "unknown",
                        "requests_per_minute": "TODO",
                        "requests_per_day": "TODO",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            _config_data(
                tmp_path,
                {"n_items": 1, "repeats": 3, "item_ids": ["mock-item-002"]},
            )
        ),
        encoding="utf-8",
    )

    plans = plan_run_counts(
        items_path,
        models_path,
        config_path,
        requested_conditions=CONDITIONS,
    )

    assert plans[0]["full_pass_requests"] == 10
    assert plans[0]["noise_extra_requests"] == 10
    assert plans[0]["days"] == 1
    assert plans[1]["requests_per_minute"] == "unknown"
    assert plans[1]["requests_per_day"] == "unknown"
    assert plans[1]["days"] == "unknown"
