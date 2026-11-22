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
    This is a population-averaged sensitivity analysis to the primary mixed model.
    """
    main = df[df["repeat"] == 1]
    rows = []
    for model, g in main.groupby("model_slug"):
        d = g[["item_id", "condition", "correct"]].copy()
        d["y"] = d["correct"].astype(int)
        d["condition"] = pd.Categorical(d["condition"], categories=CONDITIONS)

        fam = Binomial()
        cov = Exchangeable()
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
                "model_role": "sensitivity",
                "method": "GEE exchangeable, item-clustered",
                "condition_vs_NU": cond,
                "log_odds": float(mean),
                "se": float(se),
                "lo": float(lo),
                "hi": float(hi),
                "odds_ratio": float(np.exp(mean)),
                "p_value": float(p),
                "converged": bool(r.converged),
                "fit_status": "CONVERGED" if r.converged else "NON_CONVERGED",
            })
    return pd.DataFrame(rows)


def mixed_table(df, seed=42):
    """
    Per model: logistic mixed model, correct ~ condition (NU = reference) + random intercept per item.
    Variational Bayes fit: log_odds = posterior mean, sd = posterior sd.
    This is the primary regression model; GEE is reported as a sensitivity analysis.
    """
    main = df[df["repeat"] == 1]
    rows = []
    for model_index, (model, g) in enumerate(main.groupby("model_slug", sort=True)):
        d = g[["item_id", "condition", "correct"]].copy()
        d["y"] = d["correct"].astype(int)
        d["condition"] = pd.Categorical(d["condition"], categories=CONDITIONS)
        m = BinomialBayesMixedGLM.from_formula(
            "y ~ C(condition, Treatment('NU'))", {"item": "0 + C(item_id)"}, d
        )
        rng = np.random.default_rng(seed + model_index)
        r = m.fit_vb(rng=rng)
        optimizer = r.optim_retvals
        converged = bool(optimizer.success)
        for i, name in enumerate(m.exog_names):
            if name == "Intercept":
                continue
            cond = name.split("[T.")[1].rstrip("]")
            mean, sd = r.fe_mean[i], r.fe_sd[i]
            rows.append({
                "model_slug": model,
                "model_role": "primary",
                "method": "Bayesian logistic mixed model (variational Bayes)",
                "condition_vs_NU": cond,
                "log_odds": mean, "sd": sd,
                "lo": mean - 1.96 * sd, "hi": mean + 1.96 * sd,
                "odds_ratio": float(np.exp(mean)),
                "item_sd": float(np.exp(r.vcp_mean[0])),
                "converged": converged,
                "fit_status": "CONVERGED" if converged else "NON_CONVERGED",
                "optimizer_message": str(optimizer.message),
                "optimizer_iterations": int(optimizer.nit),
                "optimizer_function_evaluations": int(optimizer.nfev),
            })
    return pd.DataFrame(rows)
