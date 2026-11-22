from itertools import combinations

import numpy as np
import pandas as pd

from .bootstrap import bootstrap_mean_ci


def noise_per_item(df, conditions=None):
    """Return repeated-run pair and any-flip rates for each model/item."""
    d = df.copy()
    if conditions is not None:
        d = d[d["condition"].isin(conditions)].copy()
    keys = ["model_slug", "condition", "item_id", "repeat"]
    if d.duplicated(keys).any():
        raise ValueError("Duplicate model/condition/item/repeat rows in repeated-run data.")
    if "domain" in d.columns:
        domain_counts = d.groupby(["model_slug", "item_id"], dropna=False)["domain"].nunique(
            dropna=False
        )
        if (domain_counts > 1).any():
            raise ValueError("An item has conflicting domain values across conditions.")
    d["ans"] = d["parsed_answer"].where(d["valid"], "INVALID")
    nrep = d.groupby(["model_slug", "condition", "item_id"])["repeat"].transform("nunique")
    d = d[nrep > 1]
    if d.empty:
        raise ValueError("No repeated-run items are available for the selected conditions.")

    wide = d.pivot(index=["model_slug", "condition", "item_id"], columns="repeat", values="ans")
    if wide.isna().any().any():
        raise ValueError("Repeated-run data is incomplete for at least one item/condition.")

    reps = list(wide.columns)
    if len(reps) < 2:
        raise ValueError("At least two repeats are required for noise analysis.")
    pairs = list(combinations(reps, 2))
    pair_flips = np.column_stack(
        [(wide[a] != wide[b]).to_numpy(dtype=float) for a, b in pairs]
    )
    wide["noise_pair_flip"] = pair_flips.mean(axis=1)
    wide["noise_any_flip"] = (pair_flips.sum(axis=1) > 0).astype(float)

    per_condition = wide.reset_index()
    if "domain" in df.columns:
        domains = df.drop_duplicates(["model_slug", "item_id"])[
            ["model_slug", "item_id", "domain"]
        ]
        per_condition = per_condition.merge(
            domains, on=["model_slug", "item_id"], how="left", validate="many_to_one"
        )
    group_columns = ["model_slug", "item_id"]
    if "domain" in per_condition.columns:
        group_columns.append("domain")
    return per_condition.groupby(group_columns, as_index=False)[
        ["noise_pair_flip", "noise_any_flip"]
    ].mean()


def noise_table(df, n_boot=10000, seed=42):
    """Summarize repeated-run pair and any-flip rates per model."""
    per_item = noise_per_item(df)

    rows = []
    for group_index, (model, g) in enumerate(per_item.groupby("model_slug", sort=True)):
        n = len(g)
        row = {"model_slug": model, "n_items": n}
        strata = g["domain"].to_numpy() if "domain" in g.columns else None
        for name in ["noise_pair_flip", "noise_any_flip"]:
            x = g[name].to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean_ci(
                x, n_boot=n_boot, seed=seed + group_index, strata=strata
            )
            row[name] = x.mean()
            row[name + "_ci_low"] = ci_low
            row[name + "_ci_high"] = ci_high
        rows.append(row)
    return pd.DataFrame(rows)