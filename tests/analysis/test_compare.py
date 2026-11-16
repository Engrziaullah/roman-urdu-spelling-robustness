import pandas as pd
from src.analysis.compare import compare_to_noise


def build(data):
    # data: item -> {condition: [jawab repeat1, repeat2, ...]}
    recs = []
    for item, conds in data.items():
        for cond, answers in conds.items():
            for r, ans in enumerate(answers, start=1):
                recs.append({"model_slug": "m", "condition": cond, "item_id": item,
                             "repeat": r, "parsed_answer": ans, "valid": ans is not None})
    return pd.DataFrame(recs)


def test_known_numbers():
    df = build({
        # i1: kahin koi flip nahi
        "i1": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["A"] * 3},
        # i2: spelling flip 2/3 (repeat 1 par), noise sirf RU-X mein 2/3 -> item noise 2/9
        "i2": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["B", "B", "A"]},
        # i3: noise item nahi (sirf repeat 1), spelling flip 1.0
        "i3": {"RU-P": ["A"], "RU-R": ["B"], "RU-X": ["C"]},
    })
    r = compare_to_noise(df).iloc[0]
    assert r["n_noise_items"] == 2
    assert abs(r["spelling_flip_all"] - 5 / 9) < 1e-9
    assert abs(r["spelling_flip_noise_items"] - 1 / 3) < 1e-9
    assert abs(r["noise_flip"] - 1 / 9) < 1e-9
    assert abs(r["excess"] - 2 / 9) < 1e-9