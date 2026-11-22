import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests

from .bootstrap import bootstrap_mean_ci

CONDITIONS = ["RU-P", "RU-R", "RU-X", "RT"]


def mcnemar_table(df, cond_a="NU", cond_b="RU-P", n_boot=10000, seed=42, alpha=0.05):
    """Per model: exact McNemar (cond_a vs cond_b) + accuracy farq + CI. Holm across models."""
    if (
        "condition" not in df.columns
        or cond_a not in df["condition"].values
        or cond_b not in df["condition"].values
    ):
        raise ValueError(f"No paired predictions found for {cond_a} and {cond_b}.")
    main = df[(df["repeat"] == 1) & (df["condition"].isin([cond_a, cond_b]))]
    rows = []
    for group_index, (model, g) in enumerate(main.groupby("model_slug", sort=True)):
        if g.duplicated(["item_id", "condition"]).any():
            raise ValueError(f"{model}: duplicate item/condition prediction rows")
        w = g.pivot(index="item_id", columns="condition", values="correct")
        if (
            cond_a not in w.columns
            or cond_b not in w.columns
            or w[[cond_a, cond_b]].isna().any().any()
        ):
            raise ValueError(f"{model}: kisi item ka koi condition missing hai")
        a = w[cond_a].to_numpy(dtype=bool)
        b = w[cond_b].to_numpy(dtype=bool)
        only_a = int((a & ~b).sum())
        only_b = int((~a & b).sum())
        disc = only_a + only_b
        p = 1.0 if disc == 0 else binomtest(only_a, disc, 0.5).pvalue

        diff = a.astype(float) - b.astype(float)
        n = len(diff)
        if "domain" in g.columns:
            if g.groupby("item_id", dropna=False)["domain"].nunique(dropna=False).gt(1).any():
                raise ValueError(f"{model}: conflicting domain values across paired conditions")
            strata = (
                g.drop_duplicates("item_id").set_index("item_id").loc[w.index, "domain"].to_numpy()
            )
        else:
            strata = None
        ci_low, ci_high = bootstrap_mean_ci(
            diff, n_boot=n_boot, seed=seed + group_index, strata=strata
        )
        row = {
            "model_slug": model, "n": n,
            "condition_a": cond_a, "condition_b": cond_b,
            "acc_" + cond_a: a.mean(), "acc_" + cond_b: b.mean(),
            "only_" + cond_a: only_a, "only_" + cond_b: only_b,
            "acc_diff": diff.mean(),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_raw": p,
        }
        if "valid" in g.columns:
            validity = g.pivot(index="item_id", columns="condition", values="valid")
            row["n_invalid_" + cond_a] = int((~validity[cond_a].astype(bool)).sum())
            row["n_invalid_" + cond_b] = int((~validity[cond_b].astype(bool)).sum())
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError(f"No paired predictions found for {cond_a} and {cond_b}.")
    out["p_holm"] = multipletests(out["p_raw"], method="holm")[1]
    out["significant"] = out["p_holm"] < alpha
    return out


def mcnemar_all_conditions_table(
    df, n_boot=10000, seed=42, alpha=0.05, conditions=None
):
    """Compare NU with every other condition; skip conditions absent from data safely.

    Parameters
    ----------
    df : pd.DataFrame
        Predictions data as returned by load_data.
    n_boot : int
        Bootstrap resamples for accuracy-difference CIs.
    seed : int
        Random seed (passed through to mcnemar_table).
    alpha : float
        Family-wise significance threshold after Holm correction.
    conditions : list[str] | None
        Conditions to test against NU. Defaults to all CONDITIONS.
        Only conditions that have paired data are actually tested; the rest
        are skipped with a UserWarning.

    Returns
    -------
    pd.DataFrame
        One row per (model, tested condition). Holm correction applied only
        across conditions that produced results.

    Raises
    ------
    ValueError
        If none of the requested conditions have paired data.
    """
    import warnings

    if conditions is None:
        conditions = CONDITIONS

    tables = []
    skipped = []
    for condition in conditions:
        try:
            tables.append(
                mcnemar_table(df, "NU", condition, n_boot=n_boot, seed=seed, alpha=alpha)
            )
        except ValueError as exc:
            if "No paired predictions found" in str(exc):
                skipped.append(condition)
                warnings.warn(
                    f"Skipping condition {condition!r}: {exc}", UserWarning, stacklevel=2
                )
            else:
                raise

    if not tables:
        raise ValueError(
            "No conditions could be tested (all missing or incomplete)."
        )

    out = pd.concat(tables, ignore_index=True)
    out["p_holm"] = multipletests(out["p_raw"], method="holm")[1]
    out["significant"] = out["p_holm"] < alpha
    return out