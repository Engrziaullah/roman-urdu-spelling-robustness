import argparse
import sys
import warnings
import numpy as np
import pandas as pd

VARIANTS = ["RU-P", "RU-R", "RU-X"]


def counts_from_wide(wide):
    """wide: rows = units, columns = raters (jawab). Returns (units x categories) counts."""
    arr = wide.to_numpy()
    cats = sorted(pd.unique(arr.ravel()))
    counts = np.stack([(arr == c).sum(axis=1) for c in cats], axis=1).astype(float)
    return counts, cats


def fleiss_kappa(counts):
    counts = np.asarray(counts, dtype=float)
    N = counts.shape[0]
    n = counts[0].sum()                       # raters per unit
    p_i = ((counts ** 2).sum(axis=1) - n) / (n * (n - 1))
    p_bar = p_i.mean()
    p_j = counts.sum(axis=0) / (N * n)
    p_e = (p_j ** 2).sum()
    if p_e == 1:
        return np.nan                          # sab ne hamesha ek hi jawab diya
    return (p_bar - p_e) / (1 - p_e)


def kappa_with_ci(counts, item_ids, n_boot=10000, seed=42):
    """Point estimate + bootstrap CI. Bootstrap items par hota hai (ek item ke units saath rehte hain)."""
    counts = np.asarray(counts, dtype=float)
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
    rng = np.random.default_rng(seed)
    w = rng.multinomial(m, np.full(m, 1.0 / m), size=n_boot).astype(float)
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
        sp = g[g["repeat"] == 1].pivot(index="item_id", columns="condition", values="ans")
        if sp.isna().any().any():
            raise ValueError(f"{model}: kisi item ka koi variant missing hai")
        c_sp, _ = counts_from_wide(sp)
        k_sp, lo_sp, hi_sp = kappa_with_ci(c_sp, sp.index.to_numpy(), n_boot, seed)

        # 2) noise: units = (condition, item), raters = repeats
        nrep = g.groupby(["condition", "item_id"])["repeat"].transform("nunique")
        nz = g[nrep > 1].pivot(index=["condition", "item_id"], columns="repeat", values="ans")
        if nz.empty:
            raise ValueError(f"{model}: noise subset mein repeats nahi mile")
        if nz.isna().any().any():
            raise ValueError(f"{model}: kisi item ka koi repeat missing hai")
        c_nz, _ = counts_from_wide(nz)
        k_nz, lo_nz, hi_nz = kappa_with_ci(
            c_nz, nz.index.get_level_values("item_id").to_numpy(), n_boot, seed
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
    if len(r1) != len(r2):
        raise ValueError("Raters must have the same number of annotations.")
    n = len(r1)
    if n == 0:
        return np.nan, np.nan

    cats = sorted(set(r1).union(set(r2)))
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

    required_cols = {"item_id", "rater_1", "rater_2"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Kappa sheet missing required columns: {missing}")

    if df.empty:
        raise ValueError("Kappa sheet is empty")

    r1 = df["rater_1"].astype(str).str.strip().str.lower()
    r2 = df["rater_2"].astype(str).str.strip().str.lower()

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
        print("Cohen's kappa:   undefined (all ratings are identical).")
        print("Status: UNDEFINED (no chance-corrected agreement can be estimated).")
    elif res["passed"]:
        print(f"Cohen's kappa:   {res['cohen_kappa']:.4f}")
        print(f"Status: PASSED (>= {res['target_threshold']:.2f})")
    else:
        print(f"Cohen's kappa:   {res['cohen_kappa']:.4f}")
        print(f"Status: WARNING: Below target threshold ({res['target_threshold']:.2f}). Gate G2 requires rule revision.")


if __name__ == "__main__":
    main()
