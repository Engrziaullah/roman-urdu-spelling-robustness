import pandas as pd
from flips import flips_table, flip_rates_table


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


def test_flip_rates():
    df = build({
        "i1": ("A", "A", "A"),
        "i2": ("A", "A", "B"),
        "i3": ("A", "B", "C"),
        "i4": ("A", "A", None),
    })
    t = flip_rates_table(flips_table(df)).set_index("variant_pair")
    assert abs(t.loc["any", "flip_rate"] - 0.75) < 1e-9
    assert abs(t.loc["RU-P vs RU-R", "flip_rate"] - 0.25) < 1e-9
    assert abs(t.loc["RU-P vs RU-X", "flip_rate"] - 0.75) < 1e-9
    assert abs(t.loc["RU-R vs RU-X", "flip_rate"] - 0.75) < 1e-9