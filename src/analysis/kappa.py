import argparse
import sys
import warnings
import numpy as np
import pandas as pd

VARIANTS = ["RU-P", "RU-R", "RU-X"]


def counts_from_wide(wide):
    """wide: rows = units, columns = raters (jawab). Returns (units x categories) counts."""
    arr = wide.to_numpy()
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] < 2:
        raise ValueError("Kappa ratings must contain units and at least two raters.")
    if pd.isna(arr).any():
        raise ValueError("Kappa ratings cannot contain missing values.")
    cats = sorted(pd.unique(arr.ravel()))
    counts = np.stack([(arr == c).sum(axis=1) for c in cats], axis=1).astype(float)
    return counts, cats


def fleiss_kappa(counts):
    counts = np.asarray(counts, dtype=float)
    if (
        counts.ndim != 2
        or counts.shape[0] == 0
        or counts.shape[1] == 0
        or not np.isfinite(counts).all()
        or (counts < 0).any()
    ):
        raise ValueError("Fleiss kappa requires a non-empty matrix of finite non-negative counts.")
    N = counts.shape[0]
    n = counts[0].sum()                       # raters per unit
    if n < 2 or not np.allclose(counts.sum(axis=1), n):
        raise ValueError("Every unit must have the same count from at least two raters.")
    p_i = ((counts ** 2).sum(axis=1) - n) / (n * (n - 1))
    p_bar = p_i.mean()
    p_j = counts.sum(axis=0) / (N * n)
    p_e = (p_j ** 2).sum()
    if p_e == 1:
        return np.nan                          # sab ne hamesha ek hi jawab diya
    return (p_bar - p_e) / (1 - p_e)


def kappa_with_ci(counts, item_ids, n_boot=10000, seed=42, strata_ids=None):
    """Point estimate + bootstrap CI. Bootstrap items par hota hai (ek item ke units saath rehte hain)."""
    counts = np.asarray(counts, dtype=float)
    if counts.ndim != 2 or counts.shape[0] == 0 or len(item_ids) != len(counts):
        raise ValueError("counts and item_ids must describe the same non-empty set of units.")
    if n_boot < 1:
        raise ValueError("n_boot must be at least 1.")
    n = counts[0].sum()
    k_hat = fleiss_kappa(counts)
    p_i = ((counts ** 2).sum(axis=1) - n) / (n * (n - 1))
    ids, inv = np.unique(np.asarray(item_ids), return_inverse=True)
    m = len(ids)
    sum_p = np.bincount(inv, weights=p_i, minlength=m)
    units = np.bincount(inv, minlength=m).astype(float)
    cat = np.stack(
        [np.bincount(inv, weights=counts[:, j], minlength=m) for j in range(counts.shape[1])],
        axis=1,
    )
    if strata_ids is None:
        item_strata = np.zeros(m, dtype=int)
    else:
        strata_ids = np.asarray(strata_ids, dtype=object)
        if strata_ids.ndim != 1 or strata_ids.size != counts.shape[0]:
            raise ValueError("strata_ids must have one value for each Kappa unit.")
        strata_ids = pd.Series(strata_ids).where(pd.notna(strata_ids), "__missing_domain__").to_numpy()
        item_strata = np.empty(m, dtype=object)
        for item_index in range(m):
            unit_strata = pd.unique(strata_ids[inv == item_index])
            if len(unit_strata) != 1:
                raise ValueError("All Kappa units for an item must share one domain.")
            item_strata[item_index] = unit_strata[0]
    rng = np.random.default_rng(seed)
    w = np.zeros((n_boot, m), dtype=float)
    for label in pd.unique(item_strata):
        positions = np.flatnonzero(item_strata == label)
        w[:, positions] = rng.multinomial(
            len(positions), np.full(len(positions), 1.0 / len(positions)), size=n_boot
        )
    u = w @ units
    p_bar = (w @ sum_p) / u
    p_j = (w @ cat) / (u[:, None] * n)
    p_e = (p_j ** 2).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        boot = (p_bar - p_e) / (1 - p_e)
    boot = boot[np.isfinite(boot)]
    if boot.size == 0:
        return k_hat, np.nan, np.nan
    return k_hat, np.percentile(boot, 2.5), np.percentile(boot, 97.5)


def kappa_table(df, n_boot=10000, seed=42):
    """Per model: kappa across spelling variants (repeat 1) aur kappa across repeats (noise subset)."""
    d = df[df["condition"].isin(VARIANTS)].copy()
    d["ans"] = d["parsed_answer"].where(d["valid"], "INVALID")
    rows = []
    for model, g in d.groupby("model_slug"):
        # 1) spelling: units = items, raters = 3 variants
        main = g[g["repeat"] == 1]
        if main.duplicated(["item_id", "condition"]).any():
            raise ValueError(f"{model}: duplicate item/condition rows in spelling Kappa data")
        sp = main.pivot(index="item_id", columns="condition", values="ans")
        if sp.isna().any().any():
            raise ValueError(f"{model}: kisi item ka koi variant missing hai")
        c_sp, _ = counts_from_wide(sp)
        sp_strata = None
        if "domain" in main.columns:
            sp_strata = (
                main.drop_duplicates("item_id").set_index("item_id").loc[sp.index, "domain"].to_numpy()
            )
        k_sp, lo_sp, hi_sp = kappa_with_ci(
            c_sp, sp.index.to_numpy(), n_boot, seed, strata_ids=sp_strata
        )

        # 2) noise: units = (condition, item), raters = repeats
        nrep = g.groupby(["condition", "item_id"])["repeat"].transform("nunique")
        noise = g[nrep > 1]
        if noise.duplicated(["condition", "item_id", "repeat"]).any():
            raise ValueError(f"{model}: duplicate condition/item/repeat rows in noise Kappa data")
        nz = noise.pivot(index=["condition", "item_id"], columns="repeat", values="ans")
        if nz.empty:
            raise ValueError(f"{model}: noise subset mein repeats nahi mile")
        if nz.isna().any().any():
            raise ValueError(f"{model}: kisi item ka koi repeat missing hai")
        c_nz, _ = counts_from_wide(nz)
        nz_strata = None
        if "domain" in noise.columns:
            nz_strata = (
                noise.drop_duplicates(["condition", "item_id"])
                .set_index(["condition", "item_id"])
                .loc[nz.index, "domain"]
                .to_numpy()
            )
        k_nz, lo_nz, hi_nz = kappa_with_ci(
            c_nz,
            nz.index.get_level_values("item_id").to_numpy(),
            n_boot,
            seed,
            strata_ids=nz_strata,
        )
        rows.append({
            "model_slug": model,
            "n_items": len(sp),
            "kappa_spelling": k_sp, "sp_ci_low": lo_sp, "sp_ci_high": hi_sp,
            "n_noise_items": nz.index.get_level_values("item_id").nunique(),
            "kappa_noise": k_nz, "nz_ci_low": lo_nz, "nz_ci_high": hi_nz,
        })
    return pd.DataFrame(rows)


def cohen_kappa(r1, r2):
    """
    Computes Cohen's kappa and observed raw agreement between two raters.
    r1, r2: iterable of categorical ratings (e.g. ['y', 'n', ...]).
    Returns (kappa, raw_agreement).
    """
    r1 = np.asarray(r1)
    r2 = np.asarray(r2)
    if r1.ndim != 1 or r2.ndim != 1 or len(r1) != len(r2):
        raise ValueError("Raters must have the same number of annotations.")
    n = len(r1)
    if n == 0:
        return np.nan, np.nan
    if pd.isna(r1).any() or pd.isna(r2).any():
        raise ValueError("Rater annotations cannot be missing.")

    cats = pd.unique(np.concatenate([r1, r2]))
    po = float(np.mean(r1 == r2))
    pe = float(sum(np.mean(r1 == c) * np.mean(r2 == c) for c in cats))

    if pe == 1.0:
        k = np.nan
    else:
        k = (po - pe) / (1.0 - pe)

    return float(k), float(po)


def evaluate_kappa_sheet(sheet_path_or_df, target_threshold=0.80):
    """
    Reads a filled kappa sheet (CSV path or DataFrame), checks required columns,
    computes Cohen's kappa and raw agreement, and warns if kappa < target_threshold.
    Never modifies the input file.
    """
    if isinstance(sheet_path_or_df, (str, bytes)) or hasattr(sheet_path_or_df, "__fspath__"):
        df = pd.read_csv(sheet_path_or_df)
    else:
        df = sheet_path_or_df.copy()

    required_cols = {"item_id", "condition", "rater_1", "rater_2"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Kappa sheet missing required columns: {missing}")

    if df.empty:
        raise ValueError("Kappa sheet is empty")

    if not 0 <= target_threshold <= 1:
        raise ValueError("target_threshold must be between 0 and 1.")
    df["item_id"] = df["item_id"].astype("string").str.strip()
    df["condition"] = df["condition"].astype("string").str.strip()
    if df["item_id"].isna().any() or df["item_id"].eq("").any():
        raise ValueError("Kappa sheet contains missing or blank item_id values.")
    invalid_conditions = ~df["condition"].isin(VARIANTS)
    if invalid_conditions.any():
        raise ValueError(
            f"Kappa sheet contains {int(invalid_conditions.sum())} invalid condition value(s); "
            f"allowed: {', '.join(VARIANTS)}."
        )
    if df.duplicated(["item_id", "condition"]).any():
        duplicates = int(df.duplicated(["item_id", "condition"], keep=False).sum())
        raise ValueError(f"Kappa sheet contains {duplicates} duplicate item-condition row(s).")

    r1 = df["rater_1"].astype("string").str.strip().str.lower()
    r2 = df["rater_2"].astype("string").str.strip().str.lower()
    missing = r1.isna() | r2.isna() | r1.eq("") | r2.eq("")
    if missing.any():
        raise ValueError(f"Kappa sheet contains {int(missing.sum())} row(s) with missing ratings.")
    invalid = ~r1.isin(["y", "n"]) | ~r2.isin(["y", "n"])
    if invalid.any():
        raise ValueError(f"Kappa sheet contains {int(invalid.sum())} row(s) with labels outside y/n.")

    n = len(df)
    k, po = cohen_kappa(r1, r2)

    passed = bool(k >= target_threshold)
    if not passed and not np.isnan(k):
        warnings.warn(
            f"Cohen's kappa {k:.4f} is below the target threshold of {target_threshold:.2f} (Gate G2 requirement). "
            f"Per PLAN.md, revise rules and re-rate.",
            UserWarning,
            stacklevel=2,
        )

    return {
        "n_items": n,
        "raw_agreement": po,
        "cohen_kappa": k,
        "target_threshold": target_threshold,
        "passed": passed,
        "status": "UNDEFINED_NO_CLASS_VARIATION" if np.isnan(k) else ("PASSED" if passed else "BELOW_THRESHOLD"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate inter-rater agreement (Cohen's kappa) from a CSV sheet.")
    parser.add_argument("sheet_path", nargs="?", help="Path to filled kappa CSV sheet.")
    parser.add_argument("--sheet", dest="sheet_option", help="Path to filled kappa CSV sheet.")
    parser.add_argument("--threshold", type=float, default=0.80, help="Target kappa threshold (default: 0.80).")
    args = parser.parse_args(argv)

    if args.sheet_path and args.sheet_option:
        parser.error("Provide the sheet path either positionally or with --sheet, not both.")
    sheet_path = args.sheet_path or args.sheet_option
    if not sheet_path:
        parser.error("A kappa sheet path is required.")

    res = evaluate_kappa_sheet(sheet_path, target_threshold=args.threshold)
    print("=== Inter-Rater Agreement Evaluation ===")
    print(f"Items evaluated: {res['n_items']}")
    print(f"Raw agreement:   {res['raw_agreement']:.4f} ({res['raw_agreement'] * 100:.2f}%)")
    if np.isnan(res["cohen_kappa"]):
        print("Cohen's kappa:   undefined (insufficient class variation; expected agreement is 1.0).")
        print("Status: UNDEFINED (no chance-corrected agreement can be estimated).")
    elif res["passed"]:
        print(f"Cohen's kappa:   {res['cohen_kappa']:.4f}")
        print(f"Status: PASSED (>= {res['target_threshold']:.2f})")
    else:
        print(f"Cohen's kappa:   {res['cohen_kappa']:.4f}")
        print(f"Status: WARNING: Below target threshold ({res['target_threshold']:.2f}). Gate G2 requires rule revision.")


if __name__ == "__main__":
    main()
