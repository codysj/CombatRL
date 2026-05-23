from combatrl.core.rng import ProjectRNG


def test_same_seed_produces_same_random_sequence() -> None:
    rng_a = ProjectRNG(seed=123)
    rng_b = ProjectRNG(seed=123)

    sequence_a = [rng_a.random() for _ in range(5)]
    sequence_b = [rng_b.random() for _ in range(5)]

    assert sequence_a == sequence_b


def test_different_seeds_produce_different_sequence() -> None:
    rng_a = ProjectRNG(seed=123)
    rng_b = ProjectRNG(seed=456)

    sequence_a = [rng_a.random() for _ in range(5)]
    sequence_b = [rng_b.random() for _ in range(5)]

    assert sequence_a != sequence_b
