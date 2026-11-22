"""
Tables generator for Phase 1-3 results.
Reads results and items following docs/CONTRACTS.md schemas and writes:
  - accuracy.csv
  - accuracy_by_domain.csv
  - flips.csv
  - flip_rates.csv
  - noise.csv
  - noise_comparison.csv
  - mcnemar.csv
  - regression_mixed.csv
  - regression_gee_sensitivity.csv
  - rt_analysis.csv
  - rt_summary.csv
  - edit_distance.csv
  - errors.csv
"""

import argparse
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd

from src.analysis.accuracy import (
    accuracy_by_domain_table,
    accuracy_table,
    load_data,
)
from src.analysis.compare import compare_to_noise
from src.analysis.flips import (
    dual_flip_rates_table,
    flip_rates_table,
    flips_table,
    PAIRS,
)
from src.analysis.mcnemar import mcnemar_all_conditions_table
from src.analysis.mixed import gee_table, mixed_table
from src.analysis.noise import noise_table


def make_accuracy_table(df, n_boot=10000, seed=42):
    """Generates accuracy.csv DataFrame: model x condition."""
    return accuracy_table(df, n_boot=n_boot, seed=seed)


def make_accuracy_by_domain_table(df, n_boot=10000, seed=42):
    """Generates condition/model accuracy summaries separately by domain."""
    return accuracy_by_domain_table(df, n_boot=n_boot, seed=seed)


def make_flips_table(df):
    """Generates flips.csv DataFrame: model x item with per-variant answers and flip indicators."""
    table = flips_table(df, valid_only=False)
    return table.drop(columns=["domain"], errors="ignore")


def make_flip_rates_table(df, n_boot=10000, seed=42):
    """
    Generates both all-item and valid-only flip rates with matched noise baselines.
    """
    flips = flips_table(df, valid_only=False)
    rates = flip_rates_table(flips, n_boot=n_boot, seed=seed)
    noise = noise_table(df, n_boot=n_boot, seed=seed).set_index("model_slug")
    rates["noise_baseline"] = [
        noise.loc[model, "noise_any_flip" if pair == "any" else "noise_pair_flip"]
        for model, pair in zip(rates["model_slug"], rates["variant_pair"])
    ]
    return rates


def make_flip_rates_valid_only_table(df, n_boot=10000, seed=42):
    """Generate the valid-only flip-rate sensitivity table with excluded-item counts."""
    rates = dual_flip_rates_table(df, n_boot=n_boot, seed=seed)
    valid = rates[rates["subset"] == "valid_only"].drop(columns=["subset"])
    return valid


def _rt_detail_table(df):
    """
    Generates per-item NU/RT answer, validity, correctness, and variant-flip records.
    """
    main = df[df["repeat"] == 1].copy()
    if main.duplicated(["model_slug", "item_id", "condition"]).any():
        raise ValueError("Duplicate main-run model/item/condition rows in RT analysis.")
    nu_rt_rows = main[main["condition"].isin(["NU", "RT"])]
    condition_counts = nu_rt_rows.groupby(["model_slug", "item_id"])["condition"].nunique()
    if (condition_counts != 2).any():
        raise ValueError("Each item must have both NU and RT main-run predictions.")
    answers = nu_rt_rows.assign(
        ans=nu_rt_rows["parsed_answer"].where(nu_rt_rows["valid"], "INVALID")
    ).pivot(
        index=["model_slug", "item_id"], columns="condition", values="ans"
    ).reset_index()
    valid = nu_rt_rows.pivot(
        index=["model_slug", "item_id"], columns="condition", values="valid"
    ).reset_index()
    correct = nu_rt_rows.pivot(
        index=["model_slug", "item_id"], columns="condition", values="correct"
    ).reset_index()
    if answers[["NU", "RT"]].isna().any().any():
        raise ValueError("NU/RT answer pairs are incomplete.")

    out = answers.rename(columns={"NU": "ans_NU", "RT": "ans_RT"})
    out = out.merge(
        valid.rename(columns={"NU": "valid_NU", "RT": "valid_RT"}),
        on=["model_slug", "item_id"],
        validate="one_to_one",
    )
    out = out.merge(
        correct.rename(columns={"NU": "correct_NU", "RT": "correct_RT"}),
        on=["model_slug", "item_id"],
        validate="one_to_one",
    )
    out["both_valid"] = out["valid_NU"] & out["valid_RT"]
    out["nu_rt_answer_match_all_items"] = (out["ans_NU"] == out["ans_RT"]).astype(int)
    out["nu_rt_agree"] = np.where(
        out["both_valid"], out["nu_rt_answer_match_all_items"], np.nan
    )
    out["correctness_diff_RT_minus_NU"] = (
        out["correct_RT"].astype(int) - out["correct_NU"].astype(int)
    )

    flips = flips_table(df, valid_only=False)
    flip_cols = flips[["model_slug", "item_id", "flip_any", "flip_pairs"]].rename(
        columns={"flip_pairs": "flips_across_variants"}
    )
    return out.merge(
        flip_cols, on=["model_slug", "item_id"], how="left", validate="one_to_one"
    )


def make_rt_analysis_table(df):
    """Generate the CONTRACTS per-item NU/RT agreement table."""
    details = _rt_detail_table(df)
    columns = [
        "model_slug",
        "item_id",
        "ans_NU",
        "ans_RT",
        "nu_rt_agree",
        "flips_across_variants",
        "flip_any",
    ]
    return details[columns]


def make_rt_summary_table(df):
    """Summarize NU/RT consistency, correctness, and spelling instability by model."""
    details = _rt_detail_table(df)
    rows = []
    for model, group in details.groupby("model_slug", sort=True):
        rows.append({
            "model_slug": model,
            "n_items": len(group),
            "n_valid_both": int(group["both_valid"].sum()),
            "n_invalid_NU": int((~group["valid_NU"]).sum()),
            "n_invalid_RT": int((~group["valid_RT"]).sum()),
            "nu_rt_answer_match_rate_all_items": group[
                "nu_rt_answer_match_all_items"
            ].mean(),
            "nu_rt_answer_agreement_rate_valid_pairs": group["nu_rt_agree"].mean(),
            "accuracy_NU": group["correct_NU"].mean(),
            "accuracy_RT": group["correct_RT"].mean(),
            "accuracy_diff_RT_minus_NU": group[
                "correctness_diff_RT_minus_NU"
            ].mean(),
            "n_items_with_variant_flip": int(group["flip_any"].sum()),
            "variant_flip_rate": group["flip_any"].mean(),
            "mean_variant_pair_flips": group["flips_across_variants"].mean(),
        })
    return pd.DataFrame(rows)


def make_mcnemar_table(df, n_boot=10000, seed=42):
    """Compare NU with all other conditions, Holm-corrected over the full test family."""
    return mcnemar_all_conditions_table(df, n_boot=n_boot, seed=seed)


def make_edit_distance_table(edit_distance_path=None):
    """
    Generates edit_distance.csv DataFrame. Reads Role A's file if provided,
    otherwise outputs the template schema for the 3 variant pairs.

    When reading a CSV, validates that required columns are present and adds
    any optional columns (as NaN) if missing.

    Required columns (CONTRACTS §3): variant_pair, mean_char_edit_distance
    Optional columns: mean_normalized_edit_distance, zero_edit_distance_share

    The zero_edit_distance_share column reports the fraction of items whose
    edit distance equals zero for each pair (required by RULES.md §8).
    """
    _REQUIRED = {"variant_pair", "mean_char_edit_distance"}
    _OPTIONAL = {"mean_normalized_edit_distance", "zero_edit_distance_share"}
    _ALL_COLS = ["variant_pair", "mean_char_edit_distance",
                 "mean_normalized_edit_distance", "zero_edit_distance_share"]

    if edit_distance_path and Path(edit_distance_path).exists():
        df = pd.read_csv(edit_distance_path)
        missing = _REQUIRED - set(df.columns)
        if missing:
            raise ValueError(
                f"Edit-distance CSV is missing required columns: {sorted(missing)}"
            )
        for col in _OPTIONAL:
            if col not in df.columns:
                df[col] = np.nan
        return df[_ALL_COLS]

    if edit_distance_path:
        raise FileNotFoundError(f"Edit-distance input does not exist: {edit_distance_path}")

    rows = []
    for a, b in PAIRS:
        rows.append({
            "variant_pair": f"{a} vs {b}",
            "mean_char_edit_distance": np.nan,
            "mean_normalized_edit_distance": np.nan,
            "zero_edit_distance_share": np.nan,
        })
    return pd.DataFrame(rows)


def make_errors_table(df=None):
    """
    Generates errors.csv DataFrame: skeleton for RQ4 failure categorization.
    If df is provided, extracts failing items (correct == False, repeat == 1).
    """
    cols = ["model_slug", "item_id", "condition", "parsed_answer", "gold", "category", "note"]
    if df is None:
        return pd.DataFrame(columns=cols)
    
    main = df[df["repeat"] == 1]
    failing = main[main["correct"] == False].copy()
    failing["category"] = ""
    failing["note"] = ""
    return failing[cols]


def write_all_tables(results_path, items_path, output_dir, edit_distance_path=None, seed=42, n_boot=10000):
    """
    Reads results and items JSONL files, computes all CONTRACTS Section 3 tables,
    and writes them as CSVs to output_dir.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    df = load_data(results_path, items_path)
    
    tables = {
        "accuracy.csv": make_accuracy_table(df, n_boot=n_boot, seed=seed),
        "accuracy_by_domain.csv": make_accuracy_by_domain_table(
            df, n_boot=n_boot, seed=seed
        ),
        "flips.csv": make_flips_table(df),
        "flip_rates.csv": make_flip_rates_table(df, n_boot=n_boot, seed=seed),
        "flip_rates_valid_only.csv": make_flip_rates_valid_only_table(
            df, n_boot=n_boot, seed=seed
        ),
        "noise.csv": noise_table(df, n_boot=n_boot, seed=seed),
        "noise_comparison.csv": compare_to_noise(df, n_boot=n_boot, seed=seed),
        "mcnemar.csv": make_mcnemar_table(df, n_boot=n_boot, seed=seed),
        "regression_mixed.csv": mixed_table(df, seed=seed),
        "regression_gee_sensitivity.csv": gee_table(df),
        "rt_analysis.csv": make_rt_analysis_table(df),
        "rt_summary.csv": make_rt_summary_table(df),
        "edit_distance.csv": make_edit_distance_table(edit_distance_path),
        "errors.csv": make_errors_table(df),
    }
    
    for filename, table in tables.items():
        file_path = out / filename
        table.to_csv(file_path, index=False)
        print(f"Wrote {filename} ({len(table)} rows) -> {file_path}")
        
    return tables


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate analysis and CONTRACTS derived tables.")
    parser.add_argument("--results", type=str, required=True, help="Path to results JSONL file.")
    parser.add_argument("--items", type=str, required=True, help="Path to items JSONL file.")
    parser.add_argument("--out", type=str, default=None, help="Output directory (defaults to a temporary directory).")
    parser.add_argument("--edit-distance", type=str, default=None, help="Optional path to edit distance CSV from Role A.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for bootstrapping.")
    parser.add_argument("--n-boot", type=int, default=10000, help="Bootstrap resamples (default: 10000).")
    args = parser.parse_args(argv)
    
    output_dir = args.out or tempfile.mkdtemp(prefix="roman-urdu-tables-")
    write_all_tables(
        args.results,
        args.items,
        output_dir,
        edit_distance_path=args.edit_distance,
        seed=args.seed,
        n_boot=args.n_boot,
    )


if __name__ == "__main__":
    main()
