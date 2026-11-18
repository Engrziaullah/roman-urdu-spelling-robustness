import numpy as np
import pandas as pd


def load_data(results_path, items_path):
    """Results ko items se join karke 'gold' aur 'correct' column banata hai."""
    res = pd.read_json(results_path, lines=True)
    items = pd.read_json(items_path, lines=True)[["item_id", "condition", "gold"]]
    df = res.merge(items, on=["item_id", "condition"], how="left", validate="many_to_one")
    if df["gold"].isna().any():
        raise ValueError("Kuch results ka gold nahi mila (item_id/condition mismatch)")
    df["valid"] = df["valid"].astype(bool)
    df["correct"] = (df["parsed_answer"] == df["gold"]) & df["valid"]
    return df


def accuracy_table(df, n_boot=10000, seed=42):
    """Per model x condition: n, accuracy, ci_low, ci_high, invalid_rate (main run only, repeat==1)."""
    main = df[df["repeat"] == 1]
    rows = []
    for (model, cond), g in main.groupby(["model_slug", "condition"]):
        if g["item_id"].duplicated().any():
            raise ValueError(f"Duplicate items in {model}/{cond}")
        correct = g["correct"].to_numpy(dtype=float)
        n = len(correct)
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(n_boot, n))
        boot = correct[idx].mean(axis=1)
        rows.append({
            "model_slug": model,
            "condition": cond,
            "n": n,
            "accuracy": correct.mean(),
            "ci_low": np.percentile(boot, 2.5),
            "ci_high": np.percentile(boot, 97.5),
            "invalid_rate": 1 - g["valid"].mean(),
        })
    return pd.DataFrame(rows)