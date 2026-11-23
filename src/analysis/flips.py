"""
Flip rate analysis across Roman Urdu spelling variants (RU-P, RU-R, RU-X).

Flip definition:
An item flips for a model if the chosen answer letter is not identical across RU-P, RU-R, and RU-X.
Two handling methods for invalid (unparsable) responses are supported:
  (a) 'all_items': Invalid answers are treated as a distinct answer category ('INVALID').
  (b) 'valid_only': Restricted strictly to items where all three variants produced valid answers.
Both versions and the count of excluded items are reported.
"""

import numpy as np
import pandas as pd

from .bootstrap import bootstrap_mean_ci

VARIANTS = ["RU-P", "RU-R", "RU-X"]
PAIRS = [("RU-P", "RU-R"), ("RU-P", "RU-X"), ("RU-R", "RU-X")]


def flips_table(df, valid_only=False):
    """
    Per model x item: answer for each condition and pairwise flip indicators (repeat==1 only).
    
    Parameters:
      df: Results DataFrame containing model_slug, item_id, condition, repeat, parsed_answer, valid.
      valid_only: If True, keep only items that are valid across all three variants (RU-P, RU-R, RU-X).
                  If False, treat invalid answers as a distinct category ('INVALID').
    """
    main = df[(df["repeat"] == 1) & (df["condition"].isin(VARIANTS))].copy()
    keys = ["model_slug", "item_id"]
    if main.duplicated(keys + ["condition"]).any():
        raise ValueError("Duplicate model/item/condition rows in main-run variant predictions.")

    if "domain" in main.columns:
        domain_counts = main.groupby(keys, dropna=False)["domain"].nunique(dropna=False)
        if (domain_counts > 1).any():
            raise ValueError("An item has conflicting domain values across conditions.")
    condition_counts = main.groupby(keys)["condition"].nunique()
    if (condition_counts != len(VARIANTS)).any():
        raise ValueError("Each item must have exactly one main-run row for every Roman Urdu variant.")

    if valid_only:
        valid_counts = main.groupby(["model_slug", "item_id"])["valid"].transform("sum")
        main = main[valid_counts == len(VARIANTS)].copy()
        main["ans"] = main["parsed_answer"]
    else:
        main["ans"] = main["parsed_answer"].where(main["valid"], "INVALID")

    if main.empty:
        columns = ["model_slug", "item_id", *VARIANTS]
        if "domain" in df.columns:
            columns.append("domain")
        columns.extend([f"flip_{a}_{b}" for a, b in PAIRS])
        columns.extend(["flip_pairs", "flip_any"])
        return pd.DataFrame(columns=columns)

    wide = main.pivot(index=keys, columns="condition", values="ans")
    if wide[VARIANTS].isna().any().any():
        raise ValueError("Kisi item ka koi variant missing hai")
    wide = wide.reset_index()
    if "domain" in main.columns:
        domains = main.drop_duplicates(keys).loc[:, keys + ["domain"]]
        wide = wide.merge(domains, on=keys, how="left", validate="one_to_one")

    pair_cols = []
    for a, b in PAIRS:
        col = f"flip_{a}_{b}"
        wide[col] = (wide[a] != wide[b]).astype(int)
        pair_cols.append(col)
    wide["flip_pairs"] = wide[pair_cols].sum(axis=1)
    wide["flip_any"] = (wide["flip_pairs"] > 0).astype(int)
    return wide


def flip_rates_table(flips, n_boot=10000, seed=42):
    """Per model x variant pair: flip_rate + bootstrap 95% CI."""
    cols = {f"{a} vs {b}": f"flip_{a}_{b}" for a, b in PAIRS}
    cols["any"] = "flip_any"
    rows = []
    for group_index, (model, g) in enumerate(flips.groupby("model_slug", sort=True)):
        n = len(g)
        for name, col in cols.items():
            x = g[col].to_numpy(dtype=float)
            strata = g["domain"].to_numpy() if "domain" in g.columns else None
            if n:
                ci_low, ci_high = bootstrap_mean_ci(
                    x, n_boot=n_boot, seed=seed + group_index, strata=strata
                )
            else:
                ci_low = ci_high = np.nan
            rows.append({
                "model_slug": model, "variant_pair": name, "n": n,
                "flip_rate": x.mean(),
                "ci_low": ci_low,
                "ci_high": ci_high,
            })
    return pd.DataFrame(rows)


def dual_flip_rates_table(df, n_boot=10000, seed=42):
    """
    Computes flip rates under both versions:
      (a) 'all_items': invalid treated as distinct answer category ('INVALID')
      (b) 'valid_only': restricted strictly to items valid across all 3 variants.
    Reports n, n_excluded, invalid_rate, and bootstrap 95% CI for each model x variant pair.
    """
    rows = []
    main_var = df[(df["repeat"] == 1) & (df["condition"].isin(VARIANTS))]
    total_per_model = main_var.groupby("model_slug")["item_id"].nunique().to_dict()

    for subset_name, valid_only in [("all_items", False), ("valid_only", True)]:
        f = flips_table(df, valid_only=valid_only)
        cols = {f"{a} vs {b}": f"flip_{a}_{b}" for a, b in PAIRS}
        cols["any"] = "flip_any"
        
        for model in total_per_model:
            g = f[f["model_slug"] == model]
            n = len(g)
            n_total = total_per_model.get(model, n)
            n_excluded = n_total - n
            
            for pair_name, col in cols.items():
                x = g[col].to_numpy(dtype=float)
                strata = g["domain"].to_numpy() if "domain" in g.columns else None
                if n:
                    ci_low, ci_high = bootstrap_mean_ci(
                        x, n_boot=n_boot, seed=seed, strata=strata
                    )
                else:
                    ci_low = ci_high = np.nan
                rows.append({
                    "model_slug": model,
                    "subset": subset_name,
                    "variant_pair": pair_name,
                    "n": n,
                    "n_total": n_total,
                    "n_excluded": n_excluded,
                    "invalid_rate": n_excluded / n_total if n_total > 0 else 0.0,
                    "flip_rate": x.mean() if n else np.nan,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                })
    return pd.DataFrame(rows)
