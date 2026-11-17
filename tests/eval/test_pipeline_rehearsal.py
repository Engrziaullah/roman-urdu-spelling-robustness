from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml
import pytest

from src.eval.check_results import check_results
from src.eval.config import ModelConfig
from src.eval.run import RunInputError, RunSettings, run_pipeline
from src.eval.runlog import RESULT_FIELDS


CONDITIONS = ("NU", "RU-P", "RU-R", "RU-X", "RT")


def _write_rehearsal_items(path: Path) -> Path:
    rows = []
    for rank in (1, 2):
        labels = ["A", "B", "C", "D", "E"] if rank == 2 else ["A", "B", "C", "D"]
        for condition in CONDITIONS:
            rows.append(
                {
                    "item_id": f"mock-item-{rank:03}",
                    "source_row": f"mock-source-{rank}",
                    "domain": "MOCK",
                    "subject": "MOCK",
                    "condition": condition,
                    "question": (
                        "MOCK five-option سوال" if rank == 2 else "MOCK four-option سوال"
                    ),
                    "options": [f"اختیار {label}" for label in labels],
                    "gold": labels[-1],
                    "verified": True,
                    "sample_rank": rank,
                    "notes": "MOCK synthetic rehearsal item",
                }
            )
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _settings(prompt_path: Path) -> RunSettings:
    return RunSettings(
        seed=42,
        max_output_tokens=16,
        temperature=0.0,
        request_timeout_s=1.0,
        max_retries=0,
        max_consecutive_failures=5,
        backoff_initial_s=0.0,
        paths={"prompt_template": prompt_path},
    )


def _model() -> ModelConfig:
    return ModelConfig(
        slug="fixture",
        provider="mock",
        model_string="fixture-model",
        api_key_env="FIXTURE_KEY",
        requests_per_minute=60,
        requests_per_day=1000,
        checked_on="mock",
    )


class UrduMockProvider:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt, model_cfg, settings):
        self.calls += 1
        answer = "E" if "five-option" in prompt else "A"
        return f"جواب {answer}", 0.01, model_cfg.model_string


def test_pipeline_rehearsal_guards_five_options_resume_and_checker(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    items_path = _write_rehearsal_items(tmp_path / "mock-items.jsonl")
    prompt_path = repo_root / "tests" / "fixtures" / "mock_prompt.txt"
    settings = _settings(prompt_path)
    provider = UrduMockProvider()
    output_dir = tmp_path / "temporary-results"
    log_path = tmp_path / "RUN_LOG.md"
    frozen_marker = tmp_path / "data" / "processed" / "FROZEN.md"
    run_date = datetime.now(timezone.utc).date().isoformat()
    run_arguments = {
        "items_path": items_path,
        "model_config": _model(),
        "settings": settings,
        "provider": provider,
        "output_dir": output_dir,
        "conditions": CONDITIONS,
        "mock": False,
        "frozen_marker": frozen_marker,
        "run_log_path": log_path,
        "run_date": run_date,
        "sleep": lambda _seconds: None,
    }

    with pytest.raises(RunInputError, match="FROZEN.md"):
        run_pipeline(**run_arguments)

    frozen_marker.parent.mkdir(parents=True)
    items_hash = hashlib.sha256(
        items_path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    frozen_marker.write_text(
        f"Temporary rehearsal marker.\nitems_v1.jsonl sha256: {items_hash}\n",
        encoding="utf-8",
    )
    first = run_pipeline(**run_arguments)
    second = run_pipeline(**run_arguments)
    output_file = output_dir / "fixture" / f"{run_date}_nu_r1.jsonl"
    rows = [
        json.loads(line)
        for line in output_file.read_text(encoding="utf-8").splitlines()
    ]

    assert first.calls_made == 10
    assert second.calls_made == 0
    assert second.cache_hits == 10
    assert provider.calls == 10
    assert len(rows) == 10
    assert all(set(row) == set(RESULT_FIELDS) for row in rows)
    assert "جواب" in output_file.read_text(encoding="utf-8")
    five_option_rows = [
        row for row in rows if row["item_id"] == "mock-item-002"
    ]
    assert all(row["parsed_answer"] == "E" and row["valid"] for row in five_option_rows)
    assert all(
        row["parsed_answer"] == "A" and row["valid"]
        for row in rows
        if row["item_id"] == "mock-item-001"
    )

    models_path = tmp_path / "models.yaml"
    models_path.write_text(
        yaml.safe_dump(
            {
                "evaluated_models": [
                    {
                        "slug": "fixture",
                        "model_string": "fixture-model",
                        "requests_per_minute": 60,
                        "requests_per_day": 1000,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump({"seed": 42, "noise_subset": None}),
        encoding="utf-8",
    )
    report = check_results(output_dir, items_path, models_path, config_path)

    assert report["ok"] is True
    assert sum(
        details["rows"]
        for details in report["models"]["fixture"]["conditions"].values()
    ) == 10
    assert all(
        details["valid_rows"] == 2
        for details in report["models"]["fixture"]["conditions"].values()
    )

    with output_file.open("a", encoding="utf-8", newline="\n") as file:
        file.write(output_file.read_text(encoding="utf-8").splitlines()[0] + "\n")
    duplicate_report = check_results(output_dir, items_path, models_path, config_path)
    assert duplicate_report["ok"] is False
    assert duplicate_report["duplicate_keys"]

    retry_rows = [
        json.loads(line)
        for line in output_file.read_text(encoding="utf-8").splitlines()
    ]
    failed_attempt = dict(retry_rows[0])
    failed_attempt.update(
        error="temporary provider failure",
        parsed_answer=None,
        valid=False,
        raw_output="",
    )
    retry_rows[0] = failed_attempt
    output_file.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in retry_rows),
        encoding="utf-8",
    )
    retry_report = check_results(output_dir, items_path, models_path, config_path)

    assert retry_report["ok"] is True
    assert retry_report["retry_history_duplicates"]
    assert retry_report["models"]["fixture"]["conditions"]["NU"]["error_rows"] == 1
    assert (
        retry_report["models"]["fixture"]["conditions"]["NU"]["unresolved_error_rows"]
        == 0
    )

    retry_rows[-1].update(
        error="latest attempt failed",
        parsed_answer=None,
        valid=False,
        raw_output="",
    )
    output_file.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in retry_rows),
        encoding="utf-8",
    )
    failed_latest_report = check_results(output_dir, items_path, models_path, config_path)
    nu_report = failed_latest_report["models"]["fixture"]["conditions"]["NU"]

    assert failed_latest_report["ok"] is False
    assert nu_report["unresolved_error_rows"] == 1
    assert ["mock-item-001", "NU", 1] in nu_report["missing"]
