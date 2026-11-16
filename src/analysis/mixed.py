import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

CONDITIONS = ["NU", "RU-P", "RU-R", "RU-X", "RT"]


def mixed_table(df, seed=42):
    """Per model: logistic mixed model, correct ~ condition (NU = reference) + random intercept per item.
    Variational Bayes fit: log_odds = posterior mean, sd = posterior sd."""
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