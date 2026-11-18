import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests


def mcnemar_table(df, cond_a="NU", cond_b="RU-P", n_boot=10000, seed=42, alpha=0.05):
    """Per model: exact McNemar (cond_a vs cond_b) + accuracy farq + CI. Holm across models."""
    main = df[(df["repeat"] == 1) & (df["condition"].isin([cond_a, cond_b]))]
    rows = []
    for model, g in main.groupby("model_slug"):
        w = g.pivot(index="item_id", columns="condition", values="correct")
        if w[[cond_a, cond_b]].isna().any().any():
            raise ValueError(f"{model}: kisi item ka koi condition missing hai")
        a = w[cond_a].to_numpy(dtype=bool)
        b = w[cond_b].to_numpy(dtype=bool)
        only_a = int((a & ~b).sum())
        only_b = int((~a & b).sum())
        disc = only_a + only_b
        p = 1.0 if disc == 0 else binomtest(only_a, disc, 0.5).pvalue

        diff = a.astype(float) - b.astype(float)
        n = len(diff)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(n_boot, n))
        boot = diff[idx].mean(axis=1)
        rows.append({
            "model_slug": model, "n": n,
            "acc_" + cond_a: a.mean(), "acc_" + cond_b: b.mean(),
            "only_" + cond_a: only_a, "only_" + cond_b: only_b,
            "acc_diff": diff.mean(),
            "ci_low": np.percentile(boot, 2.5),
            "ci_high": np.percentile(boot, 97.5),
            "p_raw": p,
        })
    out = pd.DataFrame(rows)
    out["p_holm"] = multipletests(out["p_raw"], method="holm")[1]
    out["significant"] = out["p_holm"] < alpha
    return out