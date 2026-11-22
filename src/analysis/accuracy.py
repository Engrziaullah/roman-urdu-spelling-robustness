import pandas as pd

from .bootstrap import bootstrap_mean_ci


def load_data(results_path, items_path):
    """Results ko items se join karke 'gold' aur 'correct' column banata hai."""
    res = pd.read_json(results_path, lines=True)
    item_data = pd.read_json(items_path, lines=True)
    item_columns = ["item_id", "condition", "gold"]
    if "domain" in item_data.columns:
        item_columns.append("domain")
    items = item_data[item_columns]
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
    for group_index, ((model, cond), g) in enumerate(
        main.groupby(["model_slug", "condition"], sort=True)
    ):
        if g["item_id"].duplicated().any():
            raise ValueError(f"Duplicate items in {model}/{cond}")
        correct = g["correct"].to_numpy(dtype=float)
        n = len(correct)
        strata = g["domain"].to_numpy() if "domain" in g.columns else None
        ci_low, ci_high = bootstrap_mean_ci(
            correct, n_boot=n_boot, seed=seed + group_index, strata=strata
        )
        rows.append({
            "model_slug": model,
            "condition": cond,
            "n": n,
            "accuracy": correct.mean(),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "invalid_rate": 1 - g["valid"].mean(),
        })
    return pd.DataFrame(rows)


def accuracy_by_domain_table(df, n_boot=10000, seed=42):
    """Return condition/model accuracy with bootstrap CIs separately per domain."""
    if "domain" not in df.columns:
        raise ValueError("Domain-wise accuracy requires a domain column.")
    main = df[df["repeat"] == 1]
    rows = []
    for group_index, ((model, cond, domain), g) in enumerate(
        main.groupby(["model_slug", "condition", "domain"], dropna=False, sort=True)
    ):
        if g["item_id"].duplicated().any():
            raise ValueError(f"Duplicate items in {model}/{cond}/{domain}")
        correct = g["correct"].to_numpy(dtype=float)
        ci_low, ci_high = bootstrap_mean_ci(
            correct, n_boot=n_boot, seed=seed + group_index
        )
        rows.append({
            "model_slug": model,
            "condition": cond,
            "domain": domain,
            "n": len(correct),
            "accuracy": correct.mean(),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "invalid_rate": 1 - g["valid"].mean(),
        })
    return pd.DataFrame(rows)