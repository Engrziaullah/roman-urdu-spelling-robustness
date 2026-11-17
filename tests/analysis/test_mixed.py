import numpy as np
import pandas as pd
from src.analysis.mixed import mixed_table, gee_table


def build(effects, n_items=300, seed=0):
    rng = np.random.default_rng(seed)
    skill = rng.normal(0, 0.5, n_items)
    recs = []
    for i in range(n_items):
        for cond, acc in effects.items():
            logit = np.log(acc / (1 - acc)) + skill[i]
            p = 1 / (1 + np.exp(-logit))
            recs.append({"model_slug": "m", "item_id": f"i{i}", "condition": cond,
                         "repeat": 1, "correct": bool(rng.random() < p)})
    return pd.DataFrame(recs)


def test_no_effect_is_near_zero():
    df = build({c: 0.7 for c in ["NU", "RU-P", "RU-R", "RU-X", "RT"]})
    t = mixed_table(df)
    assert len(t) == 4
    assert (t["log_odds"].abs() < 0.4).all()


def test_strong_effect_has_right_sign():
    df = build({"NU": 0.9, "RU-P": 0.9, "RU-R": 0.9, "RU-X": 0.5, "RT": 0.9})
    t = mixed_table(df).set_index("condition_vs_NU")
    assert t.loc["RU-X", "log_odds"] < -1.5
    assert t.loc["RU-X", "hi"] < 0
    assert abs(t.loc["RU-P", "log_odds"]) < 0.5


def test_gee_no_effect_is_near_zero():
    df = build({c: 0.7 for c in ["NU", "RU-P", "RU-R", "RU-X", "RT"]})
    t = gee_table(df)
    assert len(t) == 4
    assert t["converged"].all()
    assert (t["log_odds"].abs() < 0.4).all()


def test_gee_strong_effect_has_right_sign():
    df = build({"NU": 0.9, "RU-P": 0.9, "RU-R": 0.9, "RU-X": 0.5, "RT": 0.9})
    t = gee_table(df).set_index("condition_vs_NU")
    assert t.loc["RU-X", "log_odds"] < -1.5
    assert t.loc["RU-X", "hi"] < 0
    assert abs(t.loc["RU-P", "log_odds"]) < 0.5
