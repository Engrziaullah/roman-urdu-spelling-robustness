from __future__ import annotations

import json

import pytest

from src.eval.runlog import RESULT_FIELDS, append_result, append_run_summary


def _row() -> dict:
    return {
        "run_id": "2026-11-16_nu_r1",
        "model_slug": "fixture",
        "model_string": "fixture-model",
        "provider": "mock",
        "date_utc": "2026-11-16T00:00:00Z",
        "item_id": "mock-item-001",
        "condition": "NU",
        "repeat": 1,
        "prompt_hash": "0" * 64,
        "raw_output": "A",
        "parsed_answer": "A",
        "valid": True,
        "latency_s": 0.1,
        "error": None,
    }


def test_result_row_has_exact_contract_fields_and_appends(tmp_path) -> None:
    output = append_result(tmp_path / "raw", "fixture", _row()["run_id"], _row())
    saved = json.loads(output.read_text(encoding="utf-8").strip())

    assert set(saved) == set(RESULT_FIELDS)
    assert saved["item_id"] == "mock-item-001"

    append_result(tmp_path / "raw", "fixture", _row()["run_id"], _row())
    assert len(output.read_text(encoding="utf-8").splitlines()) == 2


def test_result_row_rejects_extra_fields_and_unsafe_slug(tmp_path) -> None:
    row = _row()
    row["secret"] = "must not appear"
    with pytest.raises(ValueError, match="fields mismatch"):
        append_result(tmp_path, "fixture", row["run_id"], row)

    with pytest.raises(ValueError, match="model_slug"):
        append_result(tmp_path, "../fixture", _row()["run_id"], _row())


def test_run_summary_contains_required_metadata(tmp_path) -> None:
    path = tmp_path / "results" / "RUN_LOG.md"
    append_run_summary(
        path,
        date_utc="2026-11-16T00:00:00Z",
        run_id="2026-11-16_nu_r1",
        model_slug="fixture",
        model_string="fixture-model",
        calls_made=3,
        cache_hits=1,
        errors=0,
        invalid_rate=0.1,
        latency_mean_s=0.2,
        latency_min_s=0.1,
        latency_max_s=0.3,
    )

    text = path.read_text(encoding="utf-8")
    for expected in ("fixture-model", "calls=3", "cache_hits=1", "errors=0", "2026-11-16"):
        assert expected in text
