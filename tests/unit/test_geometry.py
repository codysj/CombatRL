import pytest

from combatrl.core.geometry import (
    clamp,
    clamp_position,
    distance,
    normalize_vector,
    squared_distance,
)


def test_distance_correctness() -> None:
    assert distance((0.0, 0.0), (3.0, 4.0)) == 5.0


def test_squared_distance_correctness() -> None:
    assert squared_distance((1.0, 2.0), (4.0, 6.0)) == 25.0


def test_clamp_correctness() -> None:
    assert clamp(-1.0, 0.0, 10.0) == 0.0
    assert clamp(5.0, 0.0, 10.0) == 5.0
    assert clamp(12.0, 0.0, 10.0) == 10.0


def test_clamp_position_clamps_x_and_y() -> None:
    assert clamp_position((-5.0, 70.0), 100.0, 60.0) == (0.0, 60.0)


def test_normalize_vector_handles_normal_vector() -> None:
    assert normalize_vector((3.0, 4.0)) == pytest.approx((0.6, 0.8))


def test_normalize_vector_handles_zero_vector() -> None:
    assert normalize_vector((0.0, 0.0)) == (0.0, 0.0)
