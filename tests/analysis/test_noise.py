import pandas as pd
from src.analysis.noise import noise_table


def build(data):
    # data: item -> list of jawab (repeat 1, 2, 3...); None = invalid
    recs = []
    for item, answers in data.items():
        for r, ans in enumerate(answers, start=1):
            recs.append({"model_slug": "m", "condition": "NU", "item_id": item,
                         "repeat": r, "parsed_answer": ans, "valid": ans is not None})
    return pd.DataFrame(recs)


def test_known_numbers():
    df = build({
        "i1": ["A", "A", "A"],   # koi flip nahi: pair 0, any 0
        "i2": ["A", "A", "B"],   # 2 jodiyan alag: pair 2/3, any 1
        "i3": ["A"],             # sirf 1 repeat, ignore hona chahiye
    })
    t = noise_table(df, n_boot=200).iloc[0]
    assert t["n_items"] == 2
    assert abs(t["noise_pair_flip"] - (0 + 2 / 3) / 2) < 1e-9
    assert abs(t["noise_any_flip"] - 0.5) < 1e-9


def test_invalid_counts_as_different():
    df = build({"i1": ["A", None, "A"]})   # repeat 2 invalid: 1v2 alag, 2v3 alag, 1v3 same
    t = noise_table(df, n_boot=200).iloc[0]
    assert abs(t["noise_pair_flip"] - 2 / 3) < 1e-9
    assert t["noise_any_flip"] == 1.0