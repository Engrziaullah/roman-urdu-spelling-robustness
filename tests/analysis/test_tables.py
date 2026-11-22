from pathlib import Path

import pandas as pd
import pytest

from src.analysis.accuracy import load_data
from src.analysis.tables import (
    make_accuracy_table,
    make_accuracy_by_domain_table,
    make_flips_table,
    make_flip_rates_table,
    make_flip_rates_valid_only_table,
    make_rt_analysis_table,
    make_rt_summary_table,
    make_mcnemar_table,
    make_edit_distance_table,
    make_errors_table,
    main,
    write_all_tables,
)
from src.analysis.noise import noise_table

SYNTH_ITEMS = "src/analysis/synthetic_data/items_synth.jsonl"
SYNTH_RESULTS = "src/analysis/synthetic_data/results_synth.jsonl"


@pytest.fixture(scope="module")
def synth_df():
    return load_data(SYNTH_RESULTS, SYNTH_ITEMS)


def test_make_accuracy_table(synth_df):
    table = make_accuracy_table(synth_df)
    assert set(["model_slug", "condition", "n", "accuracy", "ci_low", "ci_high", "invalid_rate"]).issubset(table.columns)
    assert len(table) == 15  # 3 models x 5 conditions


def test_make_accuracy_by_domain_table(synth_df):
    table = make_accuracy_by_domain_table(synth_df, n_boot=100)
    assert {"model_slug", "condition", "domain", "accuracy", "ci_low", "ci_high"}.issubset(
        table.columns
    )
    assert table["domain"].nunique() > 1


def test_make_flips_table(synth_df):
    table = make_flips_table(synth_df)
    assert set(["model_slug", "item_id", "RU-P", "RU-R", "RU-X", "flip_pairs", "flip_any"]).issubset(table.columns)
    assert len(table) == 1500  # 3 models x 500 items


def test_make_flip_rates_table(synth_df):
    table = make_flip_rates_table(synth_df, n_boot=200)
    assert "noise_baseline" in table.columns
    assert len(table) == 12  # CONTRACTS schema: 3 models x 4 comparisons
    assert not table["noise_baseline"].isna().all()
    noise = noise_table(synth_df, n_boot=200).set_index("model_slug")
    for model, group in table.groupby("model_slug"):
        any_rows = group[group["variant_pair"] == "any"]
        pair_rows = group[group["variant_pair"] != "any"]
        assert (any_rows["noise_baseline"] == noise.loc[model, "noise_any_flip"]).all()
        assert (pair_rows["noise_baseline"] == noise.loc[model, "noise_pair_flip"]).all()


def test_make_flip_rates_valid_only_table(synth_df):
    table = make_flip_rates_valid_only_table(synth_df, n_boot=100)
    assert len(table) == 12
    assert {"n_total", "n_excluded", "invalid_rate"}.issubset(table.columns)
    assert (table["n"] + table["n_excluded"] == table["n_total"]).all()


def test_make_rt_analysis_table(synth_df):
    table = make_rt_analysis_table(synth_df)
    assert set([
        "model_slug", "item_id", "ans_NU", "ans_RT", "nu_rt_agree",
        "flips_across_variants",
    ]).issubset(table.columns)
    assert len(table) == 1500
    invalid_pairs = (table["ans_NU"] == "INVALID") | (table["ans_RT"] == "INVALID")
    assert table.loc[invalid_pairs, "nu_rt_agree"].isna().all()
    assert set(table.loc[~invalid_pairs, "nu_rt_agree"].unique()).issubset({0, 1})


def test_rt_summary_and_mcnemar_comparisons(synth_df):
    rt = make_rt_summary_table(synth_df)
    assert len(rt) == 3
    assert {"n_valid_both", "accuracy_diff_RT_minus_NU", "variant_flip_rate"}.issubset(
        rt.columns
    )
    mcnemar = make_mcnemar_table(synth_df, n_boot=100)
    assert len(mcnemar) == 12  # 3 models x 4 comparisons against NU
    assert set(mcnemar["condition_b"]) == {"RU-P", "RU-R", "RU-X", "RT"}


def test_make_edit_distance_table():
    table = make_edit_distance_table()
    assert set([
        "variant_pair",
        "mean_char_edit_distance",
        "mean_normalized_edit_distance",
        "zero_edit_distance_share",
    ]).issubset(table.columns)
    assert len(table) == 3
    assert table["zero_edit_distance_share"].isna().all()


def test_make_edit_distance_table_validates_schema(tmp_path):
    # Missing required column 'mean_char_edit_distance'
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("variant_pair,other_col\nRU-P vs RU-R,1.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns.*mean_char_edit_distance"):
        make_edit_distance_table(str(bad_csv))


def test_make_edit_distance_table_reads_and_fills_optional(tmp_path):
    # Has only required columns
    csv_file = tmp_path / "ed_min.csv"
    csv_file.write_text(
        "variant_pair,mean_char_edit_distance\nRU-P vs RU-R,2.5\nRU-P vs RU-X,3.0\n",
        encoding="utf-8",
    )
    table = make_edit_distance_table(str(csv_file))
    assert len(table) == 2
    assert "zero_edit_distance_share" in table.columns
    assert "mean_normalized_edit_distance" in table.columns
    assert table["zero_edit_distance_share"].isna().all()
    assert table.loc[0, "mean_char_edit_distance"] == 2.5


def test_make_edit_distance_table_reads_full_csv(tmp_path):
    # Has all required and optional columns
    csv_file = tmp_path / "ed_full.csv"
    csv_file.write_text(
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance,zero_edit_distance_share\n"
        "RU-P vs RU-R,2.5,0.05,0.12\n",
        encoding="utf-8",
    )
    table = make_edit_distance_table(str(csv_file))
    assert len(table) == 1
    assert table.loc[0, "zero_edit_distance_share"] == 0.12
    assert table.loc[0, "mean_normalized_edit_distance"] == 0.05


def test_make_edit_distance_table_file_not_found():
    with pytest.raises(FileNotFoundError, match="Edit-distance input does not exist"):
        make_edit_distance_table("non_existent_file.csv")


def test_make_errors_table(synth_df):
    table = make_errors_table(synth_df)
    assert set(["model_slug", "item_id", "condition", "parsed_answer", "gold", "category", "note"]).issubset(table.columns)
    assert len(table) > 0  # Should contain failing items from synthetic data


def test_write_all_tables(synth_df, tmp_path):
    tables = write_all_tables(SYNTH_RESULTS, SYNTH_ITEMS, tmp_path, seed=42, n_boot=50)
    expected_files = [
        "accuracy.csv",
        "accuracy_by_domain.csv",
        "flips.csv",
        "flip_rates.csv",
        "flip_rates_valid_only.csv",
        "noise.csv",
        "noise_comparison.csv",
        "mcnemar.csv",
        "regression_mixed.csv",
        "regression_gee_sensitivity.csv",
        "rt_analysis.csv",
        "rt_summary.csv",
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
