import pandas as pd
from src.analysis.mcnemar import mcnemar_table


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