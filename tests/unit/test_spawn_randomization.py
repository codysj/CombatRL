"""Seeded spawn-distribution tests."""

from combatrl.envs.spawn_randomization import randomize_team_spawns
from combatrl.schemas.configs import SpawnRandomizationConfig, load_simulation_config


def test_spawn_randomization_is_seeded_bounded_and_non_mutating() -> None:
    base = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    bounds = SpawnRandomizationConfig(max_offset_x=8.0, max_offset_y=6.0)

    first = randomize_team_spawns(base, bounds, seed=17)
    repeated = randomize_team_spawns(base, bounds, seed=17)
    different = randomize_team_spawns(base, bounds, seed=18)

    assert first == repeated
    assert first != different
    assert base == load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    for base_team, randomized_team in zip(base.teams, first.teams, strict=True):
        offsets = {
            (
                randomized.spawn_position[0] - original.spawn_position[0],
                randomized.spawn_position[1] - original.spawn_position[1],
            )
            for original, randomized in zip(
                base_team.agents, randomized_team.agents, strict=True
            )
        }
        assert len(offsets) == 1
        dx, dy = offsets.pop()
        assert abs(dx) <= bounds.max_offset_x
        assert abs(dy) <= bounds.max_offset_y
        for agent in randomized_team.agents:
            assert 0.0 <= agent.spawn_position[0] <= first.arena_width
            assert 0.0 <= agent.spawn_position[1] <= first.arena_height
