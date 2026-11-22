import pandas as pd
import pytest
from src.analysis.flips import flips_table, flip_rates_table, dual_flip_rates_table


def build(rows):
    # rows: item -> (RU-P, RU-R, RU-X) jawab; None = invalid
    recs = []
    for item, answers in rows.items():
        for cond, ans in zip(["RU-P", "RU-R", "RU-X"], answers):
            recs.append({"model_slug": "m", "item_id": item, "condition": cond,
                         "repeat": 1, "parsed_answer": ans, "valid": ans is not None})
    return pd.DataFrame(recs)


def test_flip_counts():
    df = build({
        "i1": ("A", "A", "A"),    # koi flip nahi
        "i2": ("A", "A", "B"),    # 2 jodiyan alag
        "i3": ("A", "B", "C"),    # 3 jodiyan alag
        "i4": ("A", "A", None),   # invalid = alag jawab, 2 jodiyan
    })
    f = flips_table(df).set_index("item_id")
    assert f.loc["i1", "flip_pairs"] == 0 and f.loc["i1", "flip_any"] == 0
    assert f.loc["i2", "flip_pairs"] == 2
    assert f.loc["i3", "flip_pairs"] == 3
    assert f.loc["i4", "flip_pairs"] == 2 and f.loc["i4", "flip_any"] == 1


def test_flip_counts_valid_only():
    df = build({
        "i1": ("A", "A", "A"),
        "i2": ("A", "A", "B"),
        "i3": ("A", "B", "C"),
        "i4": ("A", "A", None),   # invalid item should be excluded in valid_only mode
    })
    f = flips_table(df, valid_only=True).set_index("item_id")
    assert len(f) == 3
    assert "i4" not in f.index
    assert f.loc["i1", "flip_pairs"] == 0
    assert f.loc["i2", "flip_pairs"] == 2
    assert f.loc["i3", "flip_pairs"] == 3


def test_valid_only_all_invalid_reports_zero_items():
    df = build({"i1": (None, None, None)})
    rates = dual_flip_rates_table(df, n_boot=20)
    valid = rates[rates["subset"] == "valid_only"]
    assert (valid["n"] == 0).all()
    assert valid["flip_rate"].isna().all()
    assert (valid["n_excluded"] == 1).all()


def test_duplicate_or_missing_variant_rows_are_rejected():
    df = build({"i1": ("A", "A", "A")})
    duplicate = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        flips_table(duplicate)

    missing = df[df["condition"] != "RU-X"]
    with pytest.raises(ValueError, match="every Roman Urdu variant"):
        flips_table(missing)


def test_flip_rates():
    df = build({
        "i1": ("A", "A", "A"),
        "i2": ("A", "A", "B"),
        "i3": ("A", "B", "C"),
        "i4": ("A", "A", None),
    })
    t = flip_rates_table(flips_table(df), n_boot=200).set_index("variant_pair")
    assert abs(t.loc["any", "flip_rate"] - 0.75) < 1e-9
    assert abs(t.loc["RU-P vs RU-R", "flip_rate"] - 0.25) < 1e-9
    assert abs(t.loc["RU-P vs RU-X", "flip_rate"] - 0.75) < 1e-9
    assert abs(t.loc["RU-R vs RU-X", "flip_rate"] - 0.75) < 1e-9


def test_dual_flip_rates():
    df = build({
        "i1": ("A", "A", "A"),
        "i2": ("A", "A", "B"),
        "i3": ("A", "B", "C"),
        "i4": ("A", "A", None),
    })
    res = dual_flip_rates_table(df, n_boot=500)
    assert set(res["subset"]) == {"all_items", "valid_only"}
    all_rows = res[res["subset"] == "all_items"].set_index("variant_pair")
    valid_rows = res[res["subset"] == "valid_only"].set_index("variant_pair")
    
    assert all_rows.loc["any", "n"] == 4
    assert valid_rows.loc["any", "n"] == 3
    assert valid_rows.loc["any", "n_excluded"] == 1
    assert abs(valid_rows.loc["any", "flip_rate"] - (2 / 3)) < 1e-9
