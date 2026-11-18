import pandas as pd
from src.analysis.mcnemar import mcnemar_all_pairs_table, mcnemar_table


def build():
    recs = []

    def add(model, item, nu, rup):
        recs.append({"model_slug": model, "item_id": item, "condition": "NU", "repeat": 1, "correct": nu})
        recs.append({"model_slug": model, "item_id": item, "condition": "RU-P", "repeat": 1, "correct": rup})

    # m1: 8 items NU sahi/RU-P galat, 2 items ulta
    for i in range(8):
        add("m1", f"i{i}", True, False)
    for i in range(8, 10):
        add("m1", f"i{i}", False, True)
    # m2: 1 aur 1, aur 1 item dono sahi
    add("m2", "i0", True, False)
    add("m2", "i1", False, True)
    add("m2", "i2", True, True)
    return pd.DataFrame(recs)


def build_synthetic_multi_pair():
    """Create labelled synthetic correctness outcomes for multiple pairs."""
    outcomes = {
        "m1": {
            "NU": [True] * 10 + [False] * 2,
            "RU-P": [True] * 8 + [False] * 4,
            "RU-R": [True] * 7 + [False] * 5,
            "RU-X": [True] * 6 + [False] * 6,
            "RT": [True] * 9 + [False] * 3,
        },
        "m2": {
            "NU": [True] * 6 + [False] * 6,
            "RU-P": [True] * 5 + [False] * 7,
            "RU-R": [True] * 4 + [False] * 8,
            "RU-X": [True] * 3 + [False] * 9,
            "RT": [True] * 7 + [False] * 5,
        },
    }
    return pd.DataFrame(
        [
            {
                "model_slug": model,
                "item_id": f"synthetic-{item_index}",
                "condition": condition,
                "repeat": 1,
                "correct": correct,
            }
            for model, condition_outcomes in outcomes.items()
            for condition, values in condition_outcomes.items()
            for item_index, correct in enumerate(values)
        ]
    )


def test_known_numbers():
    t = mcnemar_table(build(), n_boot=200).set_index("model_slug")
    assert t.loc["m1", "only_NU"] == 8 and t.loc["m1", "only_RU-P"] == 2
    assert abs(t.loc["m1", "p_raw"] - 0.109375) < 1e-9     # exact binomial: 112/1024
    assert abs(t.loc["m1", "acc_diff"] - 0.6) < 1e-9
    assert t.loc["m2", "p_raw"] == 1.0
    # Holm: sorted p = [0.109375, 1.0] -> adjusted [0.21875, 1.0]
    assert abs(t.loc["m1", "p_holm"] - 0.21875) < 1e-9
    assert abs(t.loc["m2", "p_holm"] - 1.0) < 1e-9
    assert not t["significant"].any()


def test_synthetic_all_pair_holm_is_at_least_per_pair_holm():
    """The family-wide adjustment includes every synthetic model-pair test."""
    df = build_synthetic_multi_pair()
    pairs = [
        ("NU", "RU-P"),
        ("NU", "RU-R"),
        ("NU", "RU-X"),
        ("NU", "RT"),
    ]

    family = mcnemar_all_pairs_table(df, pairs, n_boot=20)

    assert set(family["pair"]) == {f"{a} vs {b}" for a, b in pairs}
    for cond_a, cond_b in pairs:
        per_pair = mcnemar_table(
            df, cond_a=cond_a, cond_b=cond_b, n_boot=20
        ).set_index("model_slug")
        family_pair = family[family["pair"] == f"{cond_a} vs {cond_b}"].set_index(
            "model_slug"
        )
        assert family_pair["p_holm"].ge(per_pair["p_holm"]).all()
