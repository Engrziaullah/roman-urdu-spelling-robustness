"""
Tables generator for Phase 1-3 results.
Reads results and items following docs/CONTRACTS.md schemas and writes:
  - accuracy.csv
  - flips.csv
  - flip_rates.csv
  - rt_analysis.csv
  - edit_distance.csv
  - errors.csv
"""

import argparse
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd

from src.analysis.accuracy import load_data, accuracy_table
from src.analysis.flips import flips_table, flip_rates_table, VARIANTS, PAIRS
from src.analysis.noise import noise_table


def make_accuracy_table(df, n_boot=2000, seed=42):
    """Generates accuracy.csv DataFrame: model x condition."""
    return accuracy_table(df, n_boot=n_boot, seed=seed)


def make_flips_table(df):
    """Generates flips.csv DataFrame: model x item with per-variant answers and flip indicators."""
    return flips_table(df, valid_only=False)


def make_flip_rates_table(df, n_boot=2000, seed=42):
    """
    Generates flip_rates.csv DataFrame: model x variant pair with bootstrap CI
    and the model's noise baseline side-by-side.
    """
    flips = flips_table(df, valid_only=False)
    rates = flip_rates_table(flips, n_boot=n_boot, seed=seed)
    
    # Calculate noise baseline per model if noise subset exists
    try:
        nz = noise_table(df, n_boot=n_boot, seed=seed)
        noise_map = nz.set_index("model_slug")["noise_pair_flip"].to_dict()
    except Exception:
        noise_map = {}
        
    rates["noise_baseline"] = rates["model_slug"].map(noise_map)
    return rates


def make_rt_analysis_table(df):
    """
    Generates rt_analysis.csv DataFrame: model x item analyzing NU vs RT agreement
    against flips across Roman Urdu variants.
    """
    main = df[df["repeat"] == 1].copy()
    main["ans"] = main["parsed_answer"].where(main["valid"], "INVALID")
    
    # Pivot NU and RT answers
    nu_rt = main[main["condition"].isin(["NU", "RT"])].pivot(
        index=["model_slug", "item_id"], columns="condition", values="ans"
    ).reset_index()
    
    nu_rt["nu_rt_agree"] = (nu_rt["NU"] == nu_rt["RT"]).astype(int)
    nu_rt = nu_rt.rename(columns={"NU": "ans_NU", "RT": "ans_RT"})
    
    # Get flips across Roman Urdu variants
    try:
        flips = flips_table(df, valid_only=False)
        flips_sub = flips[["model_slug", "item_id", "flip_any", "flip_pairs"]].rename(
            columns={"flip_pairs": "flips_across_variants"}
        )
        merged = nu_rt.merge(flips_sub, on=["model_slug", "item_id"], how="left")
    except Exception:
        merged = nu_rt
        merged["flips_across_variants"] = np.nan
        merged["flip_any"] = np.nan
        
    return merged


def make_edit_distance_table(edit_distance_path=None):
    """
    Generates edit_distance.csv DataFrame. Reads Role A's file if provided,
    otherwise outputs the template schema for the 3 variant pairs.
    """
    if edit_distance_path and Path(edit_distance_path).exists():
        return pd.read_csv(edit_distance_path)
    
    rows = []
    for a, b in PAIRS:
        rows.append({
            "variant_pair": f"{a} vs {b}",
            "mean_char_edit_distance": np.nan,
            "mean_normalized_edit_distance": np.nan,
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


def write_all_tables(results_path, items_path, output_dir, edit_distance_path=None, seed=42, n_boot=2000):
    """
    Reads results and items JSONL files, computes all CONTRACTS Section 3 tables,
    and writes them as CSVs to output_dir.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    df = load_data(results_path, items_path)
    
    tables = {
        "accuracy.csv": make_accuracy_table(df, n_boot=n_boot, seed=seed),
        "flips.csv": make_flips_table(df),
        "flip_rates.csv": make_flip_rates_table(df, n_boot=n_boot, seed=seed),
        "rt_analysis.csv": make_rt_analysis_table(df),
        "edit_distance.csv": make_edit_distance_table(edit_distance_path),
        "errors.csv": make_errors_table(df),
    }
    
    for filename, table in tables.items():
        file_path = out / filename
        table.to_csv(file_path, index=False)
        print(f"Wrote {filename} ({len(table)} rows) -> {file_path}")
        
    return tables


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate CONTRACTS Section 3 derived tables.")
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
