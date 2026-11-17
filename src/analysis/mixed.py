import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.cov_struct import Exchangeable

CONDITIONS = ["NU", "RU-P", "RU-R", "RU-X", "RT"]


def gee_table(df, alpha=0.05):
    """
    Per model: GEE logistic regression with exchangeable correlation (item as clustering unit).
    Model: correct ~ condition (treatment coded with NU as reference).
    This is the pre-specified primary regression model.
    """
    main = df[df["repeat"] == 1]
    rows = []
    for model, g in main.groupby("model_slug"):
        d = g[["item_id", "condition", "correct"]].copy()
        d["y"] = d["correct"].astype(int)
        d["condition"] = pd.Categorical(d["condition"], categories=CONDITIONS)
        
        fam = Binomial()
        cov = Exchangeable()
        try:
            m = GEE.from_formula(
                "y ~ C(condition, Treatment('NU'))",
                groups="item_id",
                data=d,
                family=fam,
                cov_struct=cov,
            )
            r = m.fit()
            ci = r.conf_int(alpha=alpha)
            
            for name in r.params.index:
                if name == "Intercept":
                    continue
                cond = name.split("[T.")[1].rstrip("]")
                mean = r.params[name]
                se = r.bse[name]
                p = r.pvalues[name]
                lo = ci.loc[name, 0]
                hi = ci.loc[name, 1]
                rows.append({
                    "model_slug": model,
                    "condition_vs_NU": cond,
                    "log_odds": float(mean),
                    "se": float(se),
                    "lo": float(lo),
                    "hi": float(hi),
                    "odds_ratio": float(np.exp(mean)),
                    "p_value": float(p),
                    "converged": bool(r.converged),
                })
        except Exception as e:
            rows.append({
                "model_slug": model,
                "condition_vs_NU": "ERROR",
                "log_odds": np.nan,
                "se": np.nan,
                "lo": np.nan,
                "hi": np.nan,
                "odds_ratio": np.nan,
                "p_value": np.nan,
                "converged": False,
                "error": str(e),
            })
    return pd.DataFrame(rows)


def mixed_table(df, seed=42):
    """
    Per model: logistic mixed model, correct ~ condition (NU = reference) + random intercept per item.
    Variational Bayes fit: log_odds = posterior mean, sd = posterior sd.
    Serves as a subject-specific (item random intercept) comparison against the primary GEE model.
    """
    main = df[df["repeat"] == 1]
    rows = []
    for model, g in main.groupby("model_slug"):
        d = g[["item_id", "condition", "correct"]].copy()
        d["y"] = d["correct"].astype(int)
        d["condition"] = pd.Categorical(d["condition"], categories=CONDITIONS)
        np.random.seed(seed)
        m = BinomialBayesMixedGLM.from_formula(
            "y ~ C(condition, Treatment('NU'))", {"item": "0 + C(item_id)"}, d
        )
        r = m.fit_vb()
        for i, name in enumerate(m.exog_names):
            if name == "Intercept":
                continue
            cond = name.split("[T.")[1].rstrip("]")
            mean, sd = r.fe_mean[i], r.fe_sd[i]
            rows.append({
                "model_slug": model, "condition_vs_NU": cond,
                "log_odds": mean, "sd": sd,
                "lo": mean - 1.96 * sd, "hi": mean + 1.96 * sd,
                "odds_ratio": float(np.exp(mean)),
                "item_sd": float(np.exp(r.vcp_mean[0])),
            })
    return pd.DataFrame(rows)
