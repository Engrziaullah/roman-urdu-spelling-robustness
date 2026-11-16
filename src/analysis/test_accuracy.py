import pandas as pd
from accuracy import accuracy_table


def make_df(correct, valid):
    n = len(correct)
    return pd.DataFrame({
        "model_slug": ["m"] * n,
        "condition": ["NU"] * n,
        "repeat": [1] * n,
        "item_id": [f"i{k}" for k in range(n)],
        "correct": correct,
        "valid": valid,
    })


def test_known_numbers():
    # 10 items: 7 sahi, 3 galat (inme se 1 invalid)
    correct = [True] * 7 + [False] * 3
    valid = [True] * 9 + [False]
    t = accuracy_table(make_df(correct, valid))
    r = t.iloc[0]
    assert r["n"] == 10
    assert abs(r["accuracy"] - 0.7) < 1e-9
    assert abs(r["invalid_rate"] - 0.1) < 1e-9


def test_ci_contains_accuracy():
    correct = [True] * 40 + [False] * 60
    t = accuracy_table(make_df(correct, [True] * 100))
    r = t.iloc[0]
    assert r["ci_low"] <= r["accuracy"] <= r["ci_high"]


def test_all_correct_ci_is_one():
    t = accuracy_table(make_df([True] * 20, [True] * 20))
    r = t.iloc[0]
    assert r["ci_low"] == 1.0 and r["ci_high"] == 1.0