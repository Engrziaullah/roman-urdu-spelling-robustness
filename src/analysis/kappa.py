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


def kappa_with_ci(counts, item_ids, n_boot=2000, seed=42):
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


def kappa_table(df, n_boot=2000, seed=42):
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