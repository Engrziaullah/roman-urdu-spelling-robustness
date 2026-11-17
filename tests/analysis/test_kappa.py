import warnings
import numpy as np
import pandas as pd
import pytest
from src.analysis.kappa import counts_from_wide, fleiss_kappa, kappa_with_ci, cohen_kappa, evaluate_kappa_sheet


def test_hand_computed():
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


def test_cohen_kappa_hand_computed():
    r1 = ["y"] * 20 + ["n"] * 10
    r2 = ["y"] * 15 + ["n"] * 15
    k, po = cohen_kappa(r1, r2)
    assert abs(po - (25 / 30)) < 1e-9
    assert abs(k - (2 / 3)) < 1e-9


def test_cohen_kappa_perfect():
    r1 = ["y", "n", "y", "n", "y"]
    r2 = ["y", "n", "y", "n", "y"]
    k, po = cohen_kappa(r1, r2)
    assert k == 1.0
    assert po == 1.0


def test_evaluate_kappa_sheet():
    df = pd.DataFrame({
        "item_id": [f"umm-{i:04d}" for i in range(1, 51)],
        "condition": ["RU-P"] * 50,
        "rater_1": ["y"] * 45 + ["n"] * 5,
        "rater_2": ["y"] * 46 + ["n"] * 4,
    })
    res = evaluate_kappa_sheet(df, target_threshold=0.80)
    assert res["n_items"] == 50
    assert res["raw_agreement"] >= 0.90
    assert res["cohen_kappa"] > 0.0


def test_evaluate_kappa_sheet_warning():
    df = pd.DataFrame({
        "item_id": [f"umm-{i:04d}" for i in range(1, 11)],
        "condition": ["RU-P"] * 10,
        "rater_1": ["y", "n"] * 5,
        "rater_2": ["n", "y"] * 5,
    })
    with pytest.warns(UserWarning, match="below the target threshold"):
        res = evaluate_kappa_sheet(df, target_threshold=0.80)
    assert res["passed"] is False
    assert res["cohen_kappa"] < 0.0


def test_evaluate_kappa_sheet_missing_columns():
    df = pd.DataFrame({
        "item_id": ["umm-0001"],
        "rater_1": ["y"],
    })
    with pytest.raises(ValueError, match="missing required columns"):
        evaluate_kappa_sheet(df)
