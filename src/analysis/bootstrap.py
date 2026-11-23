import numpy as np
import pandas as pd


def bootstrap_mean_ci(values, n_boot=10000, seed=42, strata=None):
    """Return a percentile CI for the mean, resampling independently within strata."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Bootstrap values must be a non-empty one-dimensional array.")
    if n_boot < 1:
        raise ValueError("n_boot must be at least 1.")

    if strata is None:
        groups = [np.arange(values.size)]
    else:
        strata = np.asarray(strata, dtype=object)
        if strata.ndim != 1 or strata.size != values.size:
            raise ValueError("strata must have one value for each bootstrap observation.")
        strata = pd.Series(strata).where(pd.notna(strata), "__missing_domain__")
        groups = [
            np.flatnonzero(strata.to_numpy() == label)
            for label in pd.unique(strata)
        ]

    rng = np.random.default_rng(seed)
    boot_means = np.zeros(n_boot, dtype=float)
    for positions in groups:
        draws = rng.integers(0, positions.size, size=(n_boot, positions.size))
        boot_means += values[positions][draws].mean(axis=1) * positions.size
    boot_means /= values.size
    return tuple(np.percentile(boot_means, [2.5, 97.5]))
