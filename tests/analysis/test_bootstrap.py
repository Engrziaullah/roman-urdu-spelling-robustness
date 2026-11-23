import numpy as np
import pytest

from src.analysis.bootstrap import bootstrap_mean_ci


def test_stratified_bootstrap_preserves_domain_composition():
    values = np.array([0.0] * 4 + [1.0] * 4)
    domains = np.array(["easy"] * 4 + ["hard"] * 4)

    low, high = bootstrap_mean_ci(values, n_boot=500, seed=7, strata=domains)

    assert low == pytest.approx(0.5)
    assert high == pytest.approx(0.5)


def test_bootstrap_rejects_misaligned_strata():
    with pytest.raises(ValueError, match="one value for each"):
        bootstrap_mean_ci([0, 1], strata=["d0"])
