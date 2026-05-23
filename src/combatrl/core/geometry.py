"""Deterministic 2D geometry helpers."""

import math

from combatrl.core.types import Position2D, Velocity2D


def squared_distance(a: Position2D, b: Position2D) -> float:
    """Return squared Euclidean distance between two 2D points."""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def distance(a: Position2D, b: Position2D) -> float:
    """Return Euclidean distance between two 2D points."""
    return math.sqrt(squared_distance(a, b))


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value to the inclusive [min_value, max_value] range."""
    return min(max(value, min_value), max_value)


def clamp_position(position: Position2D, width: float, height: float) -> Position2D:
    """Clamp a position inside an arena with origin at (0, 0)."""
    return (clamp(position[0], 0.0, width), clamp(position[1], 0.0, height))


def normalize_vector(vector: Velocity2D) -> Velocity2D:
    """Return a unit vector, or (0.0, 0.0) for a zero-length vector."""
    magnitude = math.sqrt(vector[0] * vector[0] + vector[1] * vector[1])
    if magnitude == 0.0:
        return (0.0, 0.0)
    return (vector[0] / magnitude, vector[1] / magnitude)


def add_vectors(a: Velocity2D, b: Velocity2D) -> Velocity2D:
    """Return vector sum a + b."""
    return (a[0] + b[0], a[1] + b[1])


def subtract_vectors(a: Velocity2D, b: Velocity2D) -> Velocity2D:
    """Return vector difference a - b."""
    return (a[0] - b[0], a[1] - b[1])


def scale_vector(v: Velocity2D, scalar: float) -> Velocity2D:
    """Return vector v multiplied by scalar."""
    return (v[0] * scalar, v[1] * scalar)
