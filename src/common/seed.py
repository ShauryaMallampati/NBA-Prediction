"""Tools to make experiments reproducible (same random seed = same results)."""

import random

import numpy as np


def set_seed(seed: int = 42) -> None:
    """Lock down all randomness to get repeatable results.

    The tree models take their own `random_state`/`random_seed` parameters (set in
    `EnsembleTrainerV2`), so this only covers the stdlib and NumPy generators.
    """
    random.seed(seed)
    np.random.seed(seed)
