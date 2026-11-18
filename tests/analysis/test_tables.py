from pathlib import Path

import pandas as pd
import pytest

from src.analysis.accuracy import load_data
from src.analysis.tables import (
    make_accuracy_table,
    make_flips_table,
    make_flip_rates_table,
    make_rt_analysis_table,
    make_edit_distance_table,
    make_errors_table,
    main,
    write_all_tables,
)

SYNTH_ITEMS = "src/analysis/synthetic_data/items_synth.jsonl"
SYNTH_RESULTS = "src/analysis/synthetic_data/results_synth.jsonl"


@pytest.fixture(scope="module")
def synth_df():
    return load_data(SYNTH_RESULTS, SYNTH_ITEMS)


def test_make_accuracy_table(synth_df):
    table = make_accuracy_table(synth_df)
    assert set(["model_slug", "condition", "n", "accuracy", "ci_low", "ci_high", "invalid_rate"]).issubset(table.columns)
    assert len(table) == 15  # 3 models x 5 conditions


def test_make_flips_table(synth_df):
    table = make_flips_table(synth_df)
    assert set(["model_slug", "item_id", "RU-P", "RU-R", "RU-X", "flip_pairs", "flip_any"]).issubset(table.columns)
    assert len(table) == 1500  # 3 models x 500 items


def test_make_flip_rates_table(synth_df):
    table = make_flip_rates_table(synth_df, n_boot=200)
    assert "noise_baseline" in table.columns
    assert len(table) == 12  # 3 models x 4 pairs (3 pairs + 'any')
    assert not table["noise_baseline"].isna().all()


def test_make_rt_analysis_table(synth_df):
    table = make_rt_analysis_table(synth_df)
    assert set(["model_slug", "item_id", "ans_NU", "ans_RT", "nu_rt_agree", "flips_across_variants"]).issubset(table.columns)
    assert len(table) == 1500
    assert set(table["nu_rt_agree"].unique()).issubset({0, 1})


def test_make_edit_distance_table():
    table = make_edit_distance_table()
    assert set(["variant_pair", "mean_char_edit_distance", "mean_normalized_edit_distance"]).issubset(table.columns)
    assert len(table) == 3


def test_make_errors_table(synth_df):
    table = make_errors_table(synth_df)
    assert set(["model_slug", "item_id", "condition", "parsed_answer", "gold", "category", "note"]).issubset(table.columns)
    assert len(table) > 0  # Should contain failing items from synthetic data


def test_write_all_tables(synth_df, tmp_path):
    tables = write_all_tables(SYNTH_RESULTS, SYNTH_ITEMS, tmp_path, seed=42)
    expected_files = [
        "accuracy.csv",
        "flips.csv",
        "flip_rates.csv",
        "rt_analysis.csv",
        "edit_distance.csv",
        "errors.csv",
    ]
    for filename in expected_files:
        file_path = Path(tmp_path) / filename
        assert file_path.exists(), f"Missing output table: {filename}"
        assert file_path.stat().st_size > 0, f"Empty output table: {filename}"
        dataframe = pd.read_csv(file_path)
        assert len(dataframe) >= 0


def test_cli_parses_small_n_boot(monkeypatch, tmp_path):
    import src.analysis.tables as tables_module

    calls = {}

    def fake_write_all_tables(results_path, items_path, output_dir, **kwargs):
        calls["args"] = (results_path, items_path, output_dir)
        calls["kwargs"] = kwargs

    monkeypatch.setattr(tables_module, "write_all_tables", fake_write_all_tables)
    main([
        "--results", SYNTH_RESULTS,
        "--items", SYNTH_ITEMS,
        "--out", str(tmp_path),
        "--n-boot", "25",
    ])

    assert calls["args"] == (SYNTH_RESULTS, SYNTH_ITEMS, str(tmp_path))
    assert calls["kwargs"]["n_boot"] == 25
