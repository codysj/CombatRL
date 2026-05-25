"""Fixed-layout numeric observations for the Gymnasium wrapper."""

import numpy as np
from numpy.typing import NDArray

from combatrl.core.constants import OBSERVATION_SCHEMA_VERSION
from combatrl.core.geometry import clamp, distance
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.observations import ObservationVector

OBS_DIM = 49

FEATURE_NAMES: tuple[str, ...] = (
    "self_hp_norm",
    "self_x_norm",
    "self_y_norm",
    "self_vx_norm",
    "self_vy_norm",
    "self_attack_cd_norm",
    "self_ability_cd_norm",
    "role_tank",
    "role_ranged_dps",
    "role_support",
    "ally_alive",
    "ally_rel_x",
    "ally_rel_y",
    "ally_distance",
    "ally_hp_norm",
    "ally_role_tank",
    "ally_role_ranged_dps",
    "ally_role_support",
    "ally_threat_indicator",
    "enemy1_alive",
    "enemy1_rel_x",
    "enemy1_rel_y",
    "enemy1_distance",
    "enemy1_hp_norm",
    "enemy1_role_tank",
    "enemy1_role_ranged_dps",
    "enemy1_role_support",
    "enemy1_in_attack_range",
    "enemy2_alive",
    "enemy2_rel_x",
    "enemy2_rel_y",
    "enemy2_distance",
    "enemy2_hp_norm",
    "enemy2_role_tank",
    "enemy2_role_ranged_dps",
    "enemy2_role_support",
    "enemy2_in_attack_range",
    "wall_left_norm",
    "wall_right_norm",
    "wall_bottom_norm",
    "wall_top_norm",
    "center_rel_x",
    "center_rel_y",
    "nearest_enemy_distance",
    "nearest_ally_distance",
    "outnumbered_flag",
    "controlled_agent_recently_damaged_flag",
    "ally_recently_damaged_flag",
    "attack_ready_flag",
)


class ObservationBuilder:
    """Build deterministic, fixed-length observations from public match state."""

    def build_observation(self, state: MatchState, agent_id: str) -> ObservationVector:
        """Build one observation for an agent."""
        agent = state.agents[agent_id]
        values: list[float] = []
        values.extend(_self_features(state, agent))

        allies = _ordered_entities(state, agent, same_team=True)
        enemies = _ordered_entities(state, agent, same_team=False)

        values.extend(_ally_features(state, agent, allies[0] if allies else None))
        values.extend(_enemy_features(state, agent, enemies[0] if enemies else None))
        values.extend(_enemy_features(state, agent, enemies[1] if len(enemies) > 1 else None))
        values.extend(_arena_features(state, agent))
        values.extend(_tactical_features(state, agent, allies, enemies))

        return ObservationVector(
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            agent_id=agent_id,
            values=[float(clamp(value, -1.0, 1.0)) for value in values],
            feature_names=list(FEATURE_NAMES),
        )


def build_observation(state: MatchState, agent_id: str) -> ObservationVector:
    """Build one observation with the default builder."""
    return ObservationBuilder().build_observation(state, agent_id)


def observation_to_numpy(obs: ObservationVector) -> NDArray[np.float32]:
    """Convert a validated observation into Gymnasium's np.float32 format."""
    array = np.asarray(obs.values, dtype=np.float32)
    if array.shape != (OBS_DIM,):
        msg = f"observation shape must be ({OBS_DIM},), got {array.shape}"
        raise ValueError(msg)
    return array


def _self_features(state: MatchState, agent: AgentState) -> list[float]:
    max_speed = max(agent.movement_speed, 1.0)
    return [
        _hp_norm(agent),
        agent.position[0] / state.arena_width,
        agent.position[1] / state.arena_height,
        agent.velocity[0] / max_speed,
        agent.velocity[1] / max_speed,
        _cooldown_norm(agent.attack_cooldown_ticks, agent.attack_cooldown_max_ticks),
        _cooldown_norm(agent.ability_cooldown_ticks, agent.attack_cooldown_max_ticks),
        *_role_one_hot(agent),
    ]


def _ally_features(
    state: MatchState,
    agent: AgentState,
    ally: AgentState | None,
) -> list[float]:
    if ally is None:
        return _missing_entity_features() + [0.0]
    return [
        _alive_flag(ally),
        *_relative_features(state, agent, ally),
        _hp_norm(ally),
        *_role_one_hot(ally),
        _ally_threat_indicator(state, ally),
    ]


def _enemy_features(
    state: MatchState,
    agent: AgentState,
    enemy: AgentState | None,
) -> list[float]:
    if enemy is None:
        return _missing_entity_features() + [0.0]
    return [
        _alive_flag(enemy),
        *_relative_features(state, agent, enemy),
        _hp_norm(enemy),
        *_role_one_hot(enemy),
        float(
            enemy.alive
            and agent.alive
            and distance(agent.position, enemy.position) <= agent.attack_range
        ),
    ]


def _arena_features(state: MatchState, agent: AgentState) -> list[float]:
    center = (state.arena_width / 2.0, state.arena_height / 2.0)
    return [
        agent.position[0] / state.arena_width,
        (state.arena_width - agent.position[0]) / state.arena_width,
        (state.arena_height - agent.position[1]) / state.arena_height,
        agent.position[1] / state.arena_height,
        _relative_axis(center[0] - agent.position[0], state.arena_width),
        _relative_axis(center[1] - agent.position[1], state.arena_height),
    ]


def _tactical_features(
    state: MatchState,
    agent: AgentState,
    allies: list[AgentState],
    enemies: list[AgentState],
) -> list[float]:
    live_allies = [ally for ally in allies if ally.alive]
    live_enemies = [enemy for enemy in enemies if enemy.alive]
    nearest_enemy_distance = _distance_norm(state, agent, live_enemies[0]) if live_enemies else 1.0
    nearest_ally_distance = _distance_norm(state, agent, live_allies[0]) if live_allies else 1.0
    controlled_team_alive = 1 + len(live_allies) if agent.alive else len(live_allies)
    return [
        nearest_enemy_distance,
        nearest_ally_distance,
        float(len(live_enemies) > controlled_team_alive),
        0.0,
        0.0,
        float(agent.alive and agent.attack_cooldown_ticks == 0),
    ]


def _ordered_entities(state: MatchState, agent: AgentState, *, same_team: bool) -> list[AgentState]:
    candidates = [
        candidate
        for candidate in state.agents.values()
        if candidate.agent_id != agent.agent_id
        and (
            (candidate.team_id == agent.team_id)
            if same_team
            else (candidate.team_id != agent.team_id)
        )
    ]
    return sorted(
        candidates,
        key=lambda candidate: (
            not candidate.alive,
            distance(agent.position, candidate.position),
            candidate.agent_id,
        ),
    )


def _missing_entity_features() -> list[float]:
    return [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]


def _relative_features(
    state: MatchState,
    source: AgentState,
    target: AgentState,
) -> list[float]:
    return [
        _relative_axis(target.position[0] - source.position[0], state.arena_width),
        _relative_axis(target.position[1] - source.position[1], state.arena_height),
        _distance_norm(state, source, target),
    ]


def _relative_axis(delta: float, arena_size: float) -> float:
    return clamp(delta / max(arena_size, 1.0), -1.0, 1.0)


def _distance_norm(state: MatchState, source: AgentState, target: AgentState) -> float:
    arena_scale = max(state.arena_width, state.arena_height, 1.0)
    return clamp(distance(source.position, target.position) / arena_scale, 0.0, 1.0)


def _hp_norm(agent: AgentState) -> float:
    return clamp(agent.hp / agent.max_hp, 0.0, 1.0)


def _cooldown_norm(current: int, maximum: int) -> float:
    return clamp(current / max(maximum, 1), 0.0, 1.0)


def _alive_flag(agent: AgentState) -> float:
    return float(agent.alive)


def _role_one_hot(agent: AgentState) -> list[float]:
    return [
        float(agent.role == "tank"),
        float(agent.role == "ranged_dps"),
        float(agent.role == "support"),
    ]


def _ally_threat_indicator(state: MatchState, ally: AgentState) -> float:
    if not ally.alive:
        return 0.0
    return float(
        any(
            enemy.alive
            and enemy.team_id != ally.team_id
            and distance(enemy.position, ally.position) <= enemy.attack_range
            for enemy in state.agents.values()
        )
    )
