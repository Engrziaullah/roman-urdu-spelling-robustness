
"""
Spelling flip rate vs noise baseline comparison.

compare_to_noise() reports, per model:
  - spelling flip rates (pair-mean and any) across all items and noise-subset items only
  - noise flip rates (pair-mean and any) on the same noise-subset items
  - excess = spelling rate on noise-subset items minus noise rate (a matched comparison)
  - paired, domain-stratified bootstrap 95% CIs on each excess measure

Noise items are those where at least one Roman Urdu variant has more than one repeat.
Noise rates are computed within each condition's repeats and then averaged across conditions,
so each item contributes exactly one noise measurement regardless of which conditions are noisy.

When no noise items exist (all rows have repeat == 1), all noise-dependent columns are NaN
and a zero is reported for n_noise_items.
"""

from itertools import combinations

import numpy as np
import pandas as pd

from .flips import flips_table, VARIANTS, PAIRS


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _paired_bootstrap_excess_ci(
    spell_vals: np.ndarray,
    noise_vals: np.ndarray,
    strata: "np.ndarray | None",
    n_boot: int,
    seed: int,
) -> tuple[float, float]:
    """
    Paired percentile bootstrap CI for excess = mean(spell) - mean(noise).

    Items are resampled jointly: for each bootstrap resample, the same set of
    item indices is used for both the spelling and noise arrays. This preserves
    the within-item pairing and correctly propagates uncertainty in the matched
    difference. Domain stratification mirrors the approach in bootstrap_mean_ci:
    items are resampled independently within each stratum and the stratum-weighted
    mean is taken across the full sample.
    """
    spell_vals = np.asarray(spell_vals, dtype=float)
    noise_vals = np.asarray(noise_vals, dtype=float)
    n = len(spell_vals)

    if n == 0:
        return (np.nan, np.nan)

    if strata is None:
        groups = [np.arange(n)]
    else:
        strata = np.asarray(strata, dtype=object)
        strata_s = (
            pd.Series(strata)
            .where(pd.notna(strata), "__missing_domain__")
            .to_numpy()
        )
        groups = [
            np.flatnonzero(strata_s == label)
            for label in pd.unique(strata_s)
        ]

    rng = np.random.default_rng(seed)
    boot_spell = np.zeros(n_boot, dtype=float)
    boot_noise = np.zeros(n_boot, dtype=float)

    for positions in groups:
        m = len(positions)
        draws = rng.integers(0, m, size=(n_boot, m))

        boot_spell += spell_vals[positions][draws].mean(axis=1) * m
        boot_noise += noise_vals[positions][draws].mean(axis=1) * m

    boot_spell /= n
    boot_noise /= n

    boot_excess = boot_spell - boot_noise
    return tuple(np.percentile(boot_excess, [2.5, 97.5]))


def _noise_per_item(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-item noise flip rates.

    Returns columns:
        model_slug, item_id, noise_pair_flip, noise_any_flip[, domain]

    Only items with at least one Roman Urdu condition having more than one
    repeat are returned.
    """
    d = df[df["condition"].isin(VARIANTS)].copy()
    d["ans"] = d["parsed_answer"].where(d["valid"], "INVALID")

    nrep = (
        d.groupby(["model_slug", "condition", "item_id"])["repeat"]
        .transform("nunique")
    )
    d = d[nrep > 1]

    wide = d.pivot(
        index=["model_slug", "condition", "item_id"],
        columns="repeat",
        values="ans",
    )

    if wide.isna().any().any():
        raise ValueError(
            "Repeated-run data is incomplete: at least one "
            "(model, condition, item) is missing a repeat value."
        )

    rep_cols = list(wide.columns)
    pairs = list(combinations(rep_cols, 2))

    if not pairs:
        raise ValueError(
            "At least two distinct repeat values are required "
            "to calculate noise flip rates."
        )

    pair_flip_arr = np.column_stack([
        (wide[a] != wide[b]).to_numpy(dtype=float)
        for a, b in pairs
    ])

    wide["_pair_flip"] = pair_flip_arr.mean(axis=1)
    wide["_any_flip"] = (pair_flip_arr.sum(axis=1) > 0).astype(float)

    per_condition = wide.reset_index()[
        [
            "model_slug",
            "condition",
            "item_id",
            "_pair_flip",
            "_any_flip",
        ]
    ]

    per_item = (
        per_condition
        .groupby(["model_slug", "item_id"])[
            ["_pair_flip", "_any_flip"]
        ]
        .mean()
        .reset_index()
        .rename(
            columns={
                "_pair_flip": "noise_pair_flip",
                "_any_flip": "noise_any_flip",
            }
        )
    )

    if "domain" in df.columns:
        domain_counts = df.groupby(
            ["model_slug", "item_id"],
            dropna=False,
        )["domain"].nunique(dropna=False)

        if (domain_counts > 1).any():
            raise ValueError(
                "An item has conflicting domain values across conditions; "
                "domain must be constant per item."
            )

        domains = df.drop_duplicates(
            ["model_slug", "item_id"]
        )[["model_slug", "item_id", "domain"]]

        per_item = per_item.merge(
            domains,
            on=["model_slug", "item_id"],
            how="left",
            validate="one_to_one",
        )

    return per_item


def _has_repeats(df: pd.DataFrame) -> bool:
    """Return True if any Roman Urdu variant has more than one repeat."""
    ru = df[df["condition"].isin(VARIANTS)]

    if ru.empty:
        return False

    return (
        ru.groupby(["model_slug", "condition", "item_id"])["repeat"]
        .nunique()
        .gt(1)
        .any()
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_to_noise(
    df: pd.DataFrame,
    n_boot: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Compare spelling flip rates against the repeated-run noise baseline.

    Parameters
    ----------
    df : DataFrame
        Results following the project CONTRACTS schema, including repeat.
    n_boot : int
        Number of paired bootstrap resamples. Must be >= 1.
    seed : int
        Random seed for reproducible bootstrap confidence intervals.

    Returns
    -------
    DataFrame
        One row per model, containing spelling rates, noise rates,
        excess rates, and paired bootstrap confidence intervals.
    """
    if n_boot < 1:
        raise ValueError("n_boot must be at least 1.")

    n_pairs = len(PAIRS)

    if n_pairs == 0:
        raise ValueError("PAIRS must contain at least one condition pair.")

    # Spelling flips from the main runs (repeat == 1).
    f = flips_table(df, valid_only=False)
    f = f[
        ["model_slug", "item_id", "flip_pairs", "flip_any"]
    ].copy()

    f["spelling_pair_rate"] = f["flip_pairs"] / n_pairs

    # Build noise-per-item table.
    if _has_repeats(df):
        nz = _noise_per_item(df)
    else:
        nz = pd.DataFrame(
            columns=[
                "model_slug",
                "item_id",
                "noise_pair_flip",
                "noise_any_flip",
            ]
        )

    nan_ci = {
        "spelling_pair_mean_noise_items": np.nan,
        "noise_pair_flip": np.nan,
        "excess_pair_mean": np.nan,
        "excess_pair_ci_low": np.nan,
        "excess_pair_ci_high": np.nan,
        "spelling_flip_any_noise_items": np.nan,
        "noise_any_flip": np.nan,
        "excess_any": np.nan,
        "excess_any_ci_low": np.nan,
        "excess_any_ci_high": np.nan,
    }

    rows = []

    for model_index, (model, gf) in enumerate(
        f.groupby("model_slug", sort=True)
    ):
        spell_pair_all = gf["spelling_pair_rate"].mean()
        spell_any_all = gf["flip_any"].mean()

        gn = nz[nz["model_slug"] == model]
        n_noise = len(gn)

        if n_noise == 0:
            rows.append({
                "model_slug": model,
                "n_noise_items": 0,
                "spelling_pair_mean_all_items": spell_pair_all,
                "spelling_flip_any_all_items": spell_any_all,
                **nan_ci,
            })
            continue

        merge_cols = [
            "item_id",
            "noise_pair_flip",
            "noise_any_flip",
        ]

        if "domain" in gn.columns:
            merge_cols.append("domain")

        merged = gf.merge(
            gn[merge_cols],
            on="item_id",
            how="inner",
            validate="one_to_one",
        )

        if merged.empty:
            rows.append({
                "model_slug": model,
                "n_noise_items": 0,
                "spelling_pair_mean_all_items": spell_pair_all,
                "spelling_flip_any_all_items": spell_any_all,
                **nan_ci,
            })
            continue

        strata = (
            merged["domain"].to_numpy()
            if "domain" in merged.columns
            else None
        )

        spell_pair_arr = merged[
            "spelling_pair_rate"
        ].to_numpy(dtype=float)

        spell_any_arr = merged[
            "flip_any"
        ].to_numpy(dtype=float)

        noise_pair_arr = merged[
            "noise_pair_flip"
        ].to_numpy(dtype=float)

        noise_any_arr = merged[
            "noise_any_flip"
        ].to_numpy(dtype=float)

        # Separate reproducible seeds for each model and metric.
        pair_ci = _paired_bootstrap_excess_ci(
            spell_pair_arr,
            noise_pair_arr,
            strata,
            n_boot,
            seed + model_index * 2,
        )

        any_ci = _paired_bootstrap_excess_ci(
            spell_any_arr,
            noise_any_arr,
            strata,
            n_boot,
            seed + model_index * 2 + 1,
        )

        rows.append({
            "model_slug": model,
            "n_noise_items": len(merged),
            "spelling_pair_mean_all_items": spell_pair_all,
            "spelling_pair_mean_noise_items": spell_pair_arr.mean(),
            "noise_pair_flip": noise_pair_arr.mean(),
            "excess_pair_mean": (
                spell_pair_arr.mean() - noise_pair_arr.mean()
            ),
            "excess_pair_ci_low": pair_ci[0],
            "excess_pair_ci_high": pair_ci[1],
            "spelling_flip_any_all_items": spell_any_all,
            "spelling_flip_any_noise_items": spell_any_arr.mean(),
            "noise_any_flip": noise_any_arr.mean(),
            "excess_any": (
                spell_any_arr.mean() - noise_any_arr.mean()
            ),
            "excess_any_ci_low": any_ci[0],
            "excess_any_ci_high": any_ci[1],
        })

    return pd.DataFrame(rows)
