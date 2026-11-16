from itertools import combinations

import numpy as np
import pandas as pd

from .flips import flips_table, VARIANTS


def noise_per_item(df, conditions=VARIANTS):
    """Per model x item: repeats ke beech average flip rate (sirf diye gaye conditions par)."""
    d = df[df["condition"].isin(conditions)].copy()
    d["ans"] = d["parsed_answer"].where(d["valid"], "INVALID")
    nrep = d.groupby(["model_slug", "condition", "item_id"])["repeat"].transform("nunique")
    d = d[nrep > 1]
    if d.empty:
        raise ValueError("Noise subset mein repeats nahi mile")
    wide = d.pivot(index=["model_slug", "condition", "item_id"], columns="repeat", values="ans")
    if wide.isna().any().any():
        raise ValueError("Kisi item ka koi repeat missing hai")
    pairs = list(combinations(wide.columns, 2))
    flips = np.column_stack(
        [(wide[a] != wide[b]).to_numpy(dtype=float) for a, b in pairs]
    )
    wide["noise"] = flips.mean(axis=1)
    return wide.reset_index().groupby(["model_slug", "item_id"])["noise"].mean().reset_index()


def compare_to_noise(df, n_boot=2000, seed=42):
    """Per model: spelling flip rate vs noise flip rate, same noise-subset items, paired bootstrap."""
    f = flips_table(df)
    f["spelling"] = f["flip_pairs"] / 3          # 3 jodiyon ka average
    nz = noise_per_item(df)
    m = f.merge(nz, on=["model_slug", "item_id"], how="inner")   # sirf noise items
    rows = []
    for model, g in m.groupby("model_slug"):
        n = len(g)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(n_boot, n))
        diff = (g["spelling"] - g["noise"]).to_numpy()
        boot = diff[idx].mean(axis=1)
        rows.append({
            "model_slug": model,
            "n_noise_items": n,
            "spelling_flip_all": f.loc[f["model_slug"] == model, "spelling"].mean(),
            "spelling_flip_noise_items": g["spelling"].mean(),
            "noise_flip": g["noise"].mean(),
            "excess": diff.mean(),
            "ci_low": np.percentile(boot, 2.5),
            "ci_high": np.percentile(boot, 97.5),
        })
    return pd.DataFrame(rows)