import numpy as np
import pandas as pd
from kappa import counts_from_wide, fleiss_kappa, kappa_with_ci


def test_hand_computed():
    # 4 items, 3 raters. Haath se hisaab: Pbar = 5/12, Pe = 70/144, kappa = -5/37
    wide = pd.DataFrame(
        [["A", "A", "A"],
         ["A", "A", "B"],
         ["A", "B", "C"],
         ["A", "A", "INVALID"]]
    )
    counts, cats = counts_from_wide(wide)
    assert cats == ["A", "B", "C", "INVALID"]
    assert abs(fleiss_kappa(counts) - (-5 / 37)) < 1e-9


def test_perfect_agreement_is_one():
    wide = pd.DataFrame([["A", "A", "A"], ["B", "B", "B"], ["C", "C", "C"]])
    counts, _ = counts_from_wide(wide)
    assert abs(fleiss_kappa(counts) - 1.0) < 1e-9


def test_everyone_same_answer_is_nan():
    wide = pd.DataFrame([["A", "A", "A"]] * 5)
    counts, _ = counts_from_wide(wide)
    assert np.isnan(fleiss_kappa(counts))


def test_ci_function_matches_point_estimate():
    rng = np.random.default_rng(0)
    rows = []
    for _ in range(200):
        base = rng.choice(list("ABCD"))
        rows.append([base if rng.random() < 0.7 else rng.choice(list("ABCD")) for _ in range(3)])
    counts, _ = counts_from_wide(pd.DataFrame(rows))
    k, lo, hi = kappa_with_ci(counts, np.arange(200))
    assert abs(k - fleiss_kappa(counts)) < 1e-12
    assert lo <= hi