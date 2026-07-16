"""Deterministic spawn-distribution transforms for Gym environments."""

from combatrl.core.rng import ProjectRNG
from combatrl.schemas.configs import SimulationConfig, SpawnRandomizationConfig


def randomize_team_spawns(
    config: SimulationConfig,
    randomization: SpawnRandomizationConfig | None,
    seed: int,
) -> SimulationConfig:
    """Translate each team formation within configured and arena-safe bounds."""
    if randomization is None or (
        randomization.max_offset_x == 0.0 and randomization.max_offset_y == 0.0
    ):
        return config

    rng = ProjectRNG(seed)
    randomized_teams = []
    for team in config.teams:
        xs = [agent.spawn_position[0] for agent in team.agents]
        ys = [agent.spawn_position[1] for agent in team.agents]
        min_dx = max(-randomization.max_offset_x, -min(xs))
        max_dx = min(randomization.max_offset_x, config.arena_width - max(xs))
        min_dy = max(-randomization.max_offset_y, -min(ys))
        max_dy = min(randomization.max_offset_y, config.arena_height - max(ys))
        dx = _uniform_inclusive(rng, min_dx, max_dx)
        dy = _uniform_inclusive(rng, min_dy, max_dy)
        randomized_teams.append(
            team.model_copy(
                update={
                    "agents": [
                        agent.model_copy(
                            update={
                                "spawn_position": (
                                    agent.spawn_position[0] + dx,
                                    agent.spawn_position[1] + dy,
                                )
                            }
                        )
                        for agent in team.agents
                    ]
                }
            )
        )
    return config.model_copy(update={"teams": randomized_teams})


def _uniform_inclusive(rng: ProjectRNG, low: float, high: float) -> float:
    if low == high:
        return low
    return rng.uniform(low, high)
