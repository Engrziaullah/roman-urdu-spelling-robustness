import numpy as np
import pandas as pd

VARIANTS = ["RU-P", "RU-R", "RU-X"]
PAIRS = [("RU-P", "RU-R"), ("RU-P", "RU-X"), ("RU-R", "RU-X")]


def flips_table(df):
    """Per model x item: har condition ka jawab aur flip columns (repeat==1 only)."""
    main = df[(df["repeat"] == 1) & (df["condition"].isin(VARIANTS))].copy()
    main["ans"] = main["parsed_answer"].where(main["valid"], "INVALID")
    wide = main.pivot(index=["model_slug", "item_id"], columns="condition", values="ans")
    if wide[VARIANTS].isna().any().any():
        raise ValueError("Kisi item ka koi variant missing hai")
    wide = wide.reset_index()
    pair_cols = []
    for a, b in PAIRS:
        col = f"flip_{a}_{b}"
        wide[col] = (wide[a] != wide[b]).astype(int)
        pair_cols.append(col)
    wide["flip_pairs"] = wide[pair_cols].sum(axis=1)
    wide["flip_any"] = (wide["flip_pairs"] > 0).astype(int)
    return wide


def flip_rates_table(flips, n_boot=2000, seed=42):
    """Per model x variant pair: flip_rate + bootstrap 95% CI."""
    cols = {f"{a} vs {b}": f"flip_{a}_{b}" for a, b in PAIRS}
    cols["any"] = "flip_any"
    rows = []
    for model, g in flips.groupby("model_slug"):
        n = len(g)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(n_boot, n))
        for name, col in cols.items():
            x = g[col].to_numpy(dtype=float)
            boot = x[idx].mean(axis=1)
            rows.append({
                "model_slug": model, "variant_pair": name, "n": n,
                "flip_rate": x.mean(),
                "ci_low": np.percentile(boot, 2.5),
                "ci_high": np.percentile(boot, 97.5),
            })
    return pd.DataFrame(rows)