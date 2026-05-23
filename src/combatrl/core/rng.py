"""Deterministic project RNG wrapper."""

from collections.abc import Sequence
from typing import TypeVar

import numpy as np
from numpy.typing import NDArray

T = TypeVar("T")


class ProjectRNG:
    """Small wrapper around a seeded NumPy generator.

    Simulation code should depend on this wrapper instead of NumPy's global RNG.
    """

    def __init__(self, seed: int) -> None:
        self._seed = seed
        self._generator = np.random.default_rng(seed)

    @property
    def seed(self) -> int:
        """The explicit seed used to create this RNG."""
        return self._seed

    def random(self) -> float:
        """Return a deterministic float in the half-open interval [0.0, 1.0)."""
        return float(self._generator.random())

    def uniform(self, low: float = 0.0, high: float = 1.0) -> float:
        """Return a deterministic float sampled uniformly from [low, high)."""
        return float(self._generator.uniform(low, high))

    def integers(self, low: int, high: int | None = None) -> int:
        """Return a deterministic integer sampled from NumPy's integers API."""
        return int(self._generator.integers(low, high))

    def choice(self, values: Sequence[T]) -> T:
        """Return a deterministic item from a non-empty sequence."""
        if not values:
            msg = "choice requires a non-empty sequence"
            raise ValueError(msg)
        index = int(self._generator.integers(0, len(values)))
        return values[index]

    def random_array(self, size: int) -> NDArray[np.float64]:
        """Return a deterministic array of floats for tests and future vector code."""
        return self._generator.random(size)
