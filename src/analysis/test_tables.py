import tempfile
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
    write_all_tables,
)

SYNTH_ITEMS = "src/analysis/synthetic_data/items_synth.jsonl"
SYNTH_RESULTS = "src/analysis/synthetic_data/results_synth.jsonl"


@pytest.fixture(scope="module")
def synth_df():
    return load_data(SYNTH_RESULTS, SYNTH_ITEMS)


def test_make_accuracy_table(synth_df):
    t = make_accuracy_table(synth_df)
    assert set(["model_slug", "condition", "n", "accuracy", "ci_low", "ci_high", "invalid_rate"]).issubset(t.columns)
    assert len(t) == 15  # 3 models x 5 conditions


def test_make_flips_table(synth_df):
    t = make_flips_table(synth_df)
    assert set(["model_slug", "item_id", "RU-P", "RU-R", "RU-X", "flip_pairs", "flip_any"]).issubset(t.columns)
    assert len(t) == 1500  # 3 models x 500 items


def test_make_flip_rates_table(synth_df):
    t = make_flip_rates_table(synth_df, n_boot=200)
    assert "noise_baseline" in t.columns
    assert len(t) == 12  # 3 models x 4 pairs (3 pairs + 'any')
    assert not t["noise_baseline"].isna().all()


def test_make_rt_analysis_table(synth_df):
    t = make_rt_analysis_table(synth_df)
    assert set(["model_slug", "item_id", "ans_NU", "ans_RT", "nu_rt_agree", "flips_across_variants"]).issubset(t.columns)
    assert len(t) == 1500
    assert set(t["nu_rt_agree"].unique()).issubset({0, 1})


def test_make_edit_distance_table():
    t = make_edit_distance_table()
    assert set(["variant_pair", "mean_char_edit_distance", "mean_normalized_edit_distance"]).issubset(t.columns)
    assert len(t) == 3


def test_make_errors_table(synth_df):
    t = make_errors_table(synth_df)
    assert set(["model_slug", "item_id", "condition", "parsed_answer", "gold", "category", "note"]).issubset(t.columns)
    assert len(t) > 0  # Should contain failing items from synthetic data


def test_write_all_tables(synth_df):
    with tempfile.TemporaryDirectory() as tmpdir:
        tables = write_all_tables(SYNTH_RESULTS, SYNTH_ITEMS, tmpdir, seed=42)
        expected_files = [
            "accuracy.csv",
            "flips.csv",
            "flip_rates.csv",
            "rt_analysis.csv",
            "edit_distance.csv",
            "errors.csv",
        ]
        for fname in expected_files:
            fpath = Path(tmpdir) / fname
            assert fpath.exists(), f"Missing output table: {fname}"
            assert fpath.stat().st_size > 0, f"Empty output table: {fname}"
            df_read = pd.read_csv(fpath)
            assert len(df_read) >= 0
