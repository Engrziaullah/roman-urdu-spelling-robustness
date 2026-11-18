from itertools import combinations

import numpy as np
import pandas as pd


def noise_table(df, n_boot=10000, seed=42):
    """Noise subset (jin items ke repeats >1 hain) par: repeats ke beech flip rate, per model."""
    d = df.copy()
    d["ans"] = d["parsed_answer"].where(d["valid"], "INVALID")
    nrep = d.groupby(["model_slug", "condition", "item_id"])["repeat"].transform("nunique")
    d = d[nrep > 1]
    if d.empty:
        raise ValueError("Noise subset mein repeats nahi mile")

    wide = d.pivot(index=["model_slug", "condition", "item_id"], columns="repeat", values="ans")
    if wide.isna().any().any():
        raise ValueError("Kisi item ka koi repeat missing hai")

    reps = list(wide.columns)
    pairs = list(combinations(reps, 2))
    pair_flips = np.column_stack(
        [(wide[a] != wide[b]).to_numpy(dtype=float) for a, b in pairs]
    )
    wide["pair_rate"] = pair_flips.mean(axis=1)               # repeats ki jodiyon mein flip ka average
    wide["any_flip"] = (pair_flips.sum(axis=1) > 0).astype(float)  # kisi bhi jodi mein flip

    # har item ka average (conditions par), phir items par bootstrap
    per_item = (
        wide.reset_index()
        .groupby(["model_slug", "item_id"])[["pair_rate", "any_flip"]]
        .mean()
        .reset_index()
    )

    rows = []
    for model, g in per_item.groupby("model_slug"):
        n = len(g)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(n_boot, n))
        row = {"model_slug": model, "n_items": n}
        for col, name in [("pair_rate", "noise_pair_flip"), ("any_flip", "noise_any_flip")]:
            x = g[col].to_numpy()
            boot = x[idx].mean(axis=1)
            row[name] = x.mean()
            row[name + "_ci_low"] = np.percentile(boot, 2.5)
            row[name + "_ci_high"] = np.percentile(boot, 97.5)
        rows.append(row)
    return pd.DataFrame(rows)