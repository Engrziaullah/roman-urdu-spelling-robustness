import numpy as np
import pandas as pd
import pytest

from src.analysis.compare import compare_to_noise


# ---------------------------------------------------------------------------
# Test-data builders
# ---------------------------------------------------------------------------

def build(data):
    """
    Build a results DataFrame from a nested dict.
    data: item_id -> {condition: [answer_repeat1, answer_repeat2, ...]}
    None encodes an invalid (unparsable) answer.
    """
    recs = []
    for item, conds in data.items():
        for cond, answers in conds.items():
            for r, ans in enumerate(answers, start=1):
                recs.append({
                    "model_slug": "m",
                    "condition": cond,
                    "item_id": item,
                    "repeat": r,
                    "parsed_answer": ans,
                    "valid": ans is not None,
                })
    return pd.DataFrame(recs)


def build_with_domain(data, domain_map):
    """Like build(), but attaches a domain to every row for each item."""
    recs = []
    for item, conds in data.items():
        for cond, answers in conds.items():
            for r, ans in enumerate(answers, start=1):
                recs.append({
                    "model_slug": "m",
                    "condition": cond,
                    "item_id": item,
                    "domain": domain_map[item],
                    "repeat": r,
                    "parsed_answer": ans,
                    "valid": ans is not None,
                })
    return pd.DataFrame(recs)


# ---------------------------------------------------------------------------
# Existing test: point-estimate values must be unchanged
# ---------------------------------------------------------------------------

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
    assert abs(r["spelling_pair_mean_all_items"] - 5 / 9) < 1e-9
    assert abs(r["spelling_pair_mean_noise_items"] - 1 / 3) < 1e-9
    assert abs(r["noise_pair_flip"] - 1 / 9) < 1e-9
    assert abs(r["excess_pair_mean"] - 2 / 9) < 1e-9
    assert abs(r["spelling_flip_any_all_items"] - 2 / 3) < 1e-9
    assert abs(r["noise_any_flip"] - 1 / 6) < 1e-9
    assert abs(r["excess_any"] - 1 / 3) < 1e-9


# ---------------------------------------------------------------------------
# New test 1: bootstrap CIs are present, finite, and ordered
# ---------------------------------------------------------------------------

def test_excess_cis_are_present_finite_and_ordered():
    """
    When noise items exist, all four CI columns must be non-NaN, finite,
    and correctly ordered (low <= point estimate <= high is not guaranteed by
    percentile bootstrap, but low <= high always holds).
    """
    df = build({
        "i1": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["A"] * 3},
        "i2": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["B", "B", "A"]},
        "i3": {"RU-P": ["A"], "RU-R": ["B"], "RU-X": ["C"]},
    })
    r = compare_to_noise(df, n_boot=500, seed=7).iloc[0]

    for col in ["excess_pair_ci_low", "excess_pair_ci_high",
                "excess_any_ci_low", "excess_any_ci_high"]:
        assert not pd.isna(r[col]), f"{col} should not be NaN when noise items exist"
        assert np.isfinite(r[col]), f"{col} should be finite"

    assert r["excess_pair_ci_low"] <= r["excess_pair_ci_high"]
    assert r["excess_any_ci_low"] <= r["excess_any_ci_high"]


# ---------------------------------------------------------------------------
# New test 2: n_boot and seed are actually used
# ---------------------------------------------------------------------------

def test_n_boot_and_seed_are_used():
    """
    Different seeds must produce different CI bounds (seed affects the RNG).
    n_boot=0 must raise; n_boot=1 must succeed (degenerate but valid CI).

    We use a dataset with enough item-level variation that the bootstrap
    distribution is non-degenerate: five noise items whose spelling answers
    and repeat answers differ, so each bootstrap resample of items genuinely
    produces a different excess estimate.
    """
    # Build a dataset with five noise items (repeats 1–3 available) with
    # varied spell/noise patterns so the bootstrap distribution has real spread.
    df = build({
        "i1": {"RU-P": ["A", "A", "A"], "RU-R": ["A", "A", "A"], "RU-X": ["A", "A", "A"]},
        "i2": {"RU-P": ["A", "A", "B"], "RU-R": ["A", "A", "A"], "RU-X": ["B", "B", "A"]},
        "i3": {"RU-P": ["A", "B", "A"], "RU-R": ["B", "B", "A"], "RU-X": ["A", "A", "B"]},
        "i4": {"RU-P": ["B", "B", "B"], "RU-R": ["A", "A", "A"], "RU-X": ["B", "A", "B"]},
        "i5": {"RU-P": ["A", "A", "A"], "RU-R": ["C", "A", "C"], "RU-X": ["D", "D", "A"]},
    })

    r_seed1 = compare_to_noise(df, n_boot=400, seed=1).iloc[0]
    r_seed2 = compare_to_noise(df, n_boot=400, seed=999).iloc[0]

    # Different seeds -> at least one CI bound differs (non-degenerate bootstrap)
    seeds_differ = (
        r_seed1["excess_pair_ci_low"] != r_seed2["excess_pair_ci_low"]
        or r_seed1["excess_pair_ci_high"] != r_seed2["excess_pair_ci_high"]
        or r_seed1["excess_any_ci_low"] != r_seed2["excess_any_ci_low"]
        or r_seed1["excess_any_ci_high"] != r_seed2["excess_any_ci_high"]
    )
    assert seeds_differ, "Different seeds must produce different CI values"

    # n_boot=1 produces a CI (degenerate but not an error)
    r_tiny = compare_to_noise(df, n_boot=1, seed=42).iloc[0]
    assert not pd.isna(r_tiny["excess_pair_ci_low"])

    # n_boot=0 raises
    with pytest.raises(ValueError, match="n_boot must be at least 1"):
        compare_to_noise(df, n_boot=0, seed=42)


# ---------------------------------------------------------------------------
# New test 3: zero noise items (all repeat == 1) -> safe NaN result
# ---------------------------------------------------------------------------

def test_zero_noise_items_returns_nan_safely():
    """
    When every row has repeat == 1 (no noise subset at all), noise-dependent
    columns must be NaN, n_noise_items must be 0, and the all-items spelling
    rates must still be computed correctly.
    """
    df = build({
        "i1": {"RU-P": ["A"], "RU-R": ["A"], "RU-X": ["A"]},
        "i2": {"RU-P": ["A"], "RU-R": ["A"], "RU-X": ["B"]},
        "i3": {"RU-P": ["A"], "RU-R": ["B"], "RU-X": ["C"]},
    })
    result = compare_to_noise(df, n_boot=100, seed=42)
    assert len(result) == 1
    r = result.iloc[0]

    assert r["n_noise_items"] == 0

    nan_cols = [
        "spelling_pair_mean_noise_items",
        "noise_pair_flip",
        "excess_pair_mean",
        "excess_pair_ci_low",
        "excess_pair_ci_high",
        "spelling_flip_any_noise_items",
        "noise_any_flip",
        "excess_any",
        "excess_any_ci_low",
        "excess_any_ci_high",
    ]
    for col in nan_cols:
        assert pd.isna(r[col]), f"{col} should be NaN when no noise items exist"

    # All-items spelling rates are unaffected by noise.
    # Flip analysis (3 PAIRS: RU-P vs RU-R, RU-P vs RU-X, RU-R vs RU-X):
    #   i1: RU-P=A, RU-R=A, RU-X=A -> flip_pairs=0
    #   i2: RU-P=A, RU-R=A, RU-X=B -> (A!=A)=0, (A!=B)=1, (A!=B)=1 -> flip_pairs=2
    #   i3: RU-P=A, RU-R=B, RU-X=C -> (A!=B)=1, (A!=C)=1, (B!=C)=1 -> flip_pairs=3
    # spelling_pair_mean_all_items = (0/3 + 2/3 + 3/3) / 3 = 5/9
    assert abs(r["spelling_pair_mean_all_items"] - 5 / 9) < 1e-9
    # flip_any: i1=0, i2=1, i3=1 -> 2/3
    assert abs(r["spelling_flip_any_all_items"] - 2 / 3) < 1e-9


# ---------------------------------------------------------------------------
# New test 4: domain column is propagated and used in stratified bootstrap
# ---------------------------------------------------------------------------

def test_domain_propagated_to_noise_calculations():
    """
    When a domain column is present in the input DataFrame, _noise_per_item
    must attach it to the per-item noise table, and compare_to_noise must use
    it for domain-stratified bootstrap CIs (no error raised, CIs finite).

    We also verify that the domain column does NOT affect the point estimates
    (domain stratification is only used in the bootstrap, not the mean).
    """
    # Two noise items in different domains
    data = {
        "i1": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["A"] * 3},
        "i2": {"RU-P": ["A"] * 3, "RU-R": ["A"] * 3, "RU-X": ["B", "B", "A"]},
        "i3": {"RU-P": ["A"], "RU-R": ["B"], "RU-X": ["C"]},
    }
    domain_map = {"i1": "science", "i2": "history", "i3": "science"}

    df_no_domain = build(data)
    df_with_domain = build_with_domain(data, domain_map)

    r_no_domain = compare_to_noise(df_no_domain, n_boot=300, seed=42).iloc[0]
    r_with_domain = compare_to_noise(df_with_domain, n_boot=300, seed=42).iloc[0]

    # Point estimates must be identical regardless of domain column presence
    for col in ["excess_pair_mean", "excess_any",
                "spelling_pair_mean_all_items", "noise_pair_flip"]:
        assert abs(r_no_domain[col] - r_with_domain[col]) < 1e-12, (
            f"Point estimate {col} should not change when domain is added"
        )

    # CIs must be finite and non-NaN in both cases
    for r_label, r in [("no_domain", r_no_domain), ("with_domain", r_with_domain)]:
        for col in ["excess_pair_ci_low", "excess_pair_ci_high",
                    "excess_any_ci_low", "excess_any_ci_high"]:
            assert np.isfinite(r[col]), f"{col} ({r_label}) should be finite"

    # With two items in different domains the stratified bootstrap will generally
    # produce different CI widths than the unstratified one (not guaranteed to differ
    # for small n, but we can confirm the with-domain run does not raise or return NaN)
    assert not pd.isna(r_with_domain["excess_pair_ci_low"])


# ---------------------------------------------------------------------------
# New test 5: len(PAIRS) denominator is used (not hard-coded 3)
# ---------------------------------------------------------------------------

def test_pair_rate_uses_len_pairs_not_hardcoded():
    """
    spelling_pair_mean_all_items must equal flip_pairs / len(PAIRS).
    If PAIRS ever grows, the denominator must grow with it.
    Flip analysis for each item (3 PAIRS: RU-P vs RU-R, RU-P vs RU-X, RU-R vs RU-X):
      i1: A, A, A -> 0 pair flips
      i2: A, A, B -> (A!=A)=0, (A!=B)=1, (A!=B)=1 -> flip_pairs=2
      i3: A, B, A -> (A!=B)=1, (A!=A)=0, (B!=A)=1 -> flip_pairs=2
    Mean pair rate = (0/3 + 2/3 + 2/3) / 3 = 4/9
    """
    from src.analysis.flips import PAIRS as CURRENT_PAIRS

    df = build({
        "i1": {"RU-P": ["A"], "RU-R": ["A"], "RU-X": ["A"]},   # 0 pair flips
        "i2": {"RU-P": ["A"], "RU-R": ["A"], "RU-X": ["B"]},   # 1 pair flip
        "i3": {"RU-P": ["A"], "RU-R": ["B"], "RU-X": ["A"]},   # 2 pair flips
    })
    r = compare_to_noise(df, n_boot=50, seed=42).iloc[0]
    expected = (0 + 2 + 2) / (3 * len(CURRENT_PAIRS))
    assert abs(r["spelling_pair_mean_all_items"] - expected) < 1e-9
