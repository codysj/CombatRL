import math

import numpy as np
from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.envs.observation_builder import (
    FEATURE_NAMES,
    OBS_DIM,
    ObservationBuilder,
    observation_to_numpy,
)

CONTROLLED_AGENT_ID = "team0_ranged_dps_0"


def _feature_index(name: str) -> int:
    return FEATURE_NAMES.index(name)


def test_observation_length_and_feature_names_match() -> None:
    observation = ObservationBuilder().build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert len(observation.values) == OBS_DIM
    assert len(observation.feature_names) == OBS_DIM


def test_observation_has_no_nan_or_infinity() -> None:
    observation = ObservationBuilder().build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert all(math.isfinite(value) for value in observation.values)
    assert np.isfinite(observation_to_numpy(observation)).all()


def test_observation_values_are_inside_box_bounds() -> None:
    observation = ObservationBuilder().build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert all(-1.0 <= value <= 1.0 for value in observation.values)


def test_self_hp_normalized_correctly() -> None:
    state = make_state()
    state.agents[CONTROLLED_AGENT_ID].hp = 45.0

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("self_hp_norm")] == 0.5


def test_entity_slots_sorted_deterministically() -> None:
    observation = ObservationBuilder().build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("enemy1_role_ranged_dps")] == 1.0
    assert observation.values[_feature_index("enemy2_role_tank")] == 1.0


def test_missing_entity_slots_filled_consistently() -> None:
    state = make_state()
    del state.agents["team0_tank_0"]
    del state.agents["team1_tank_0"]
    del state.agents["team1_ranged_dps_0"]

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("ally_alive")] == 0.0
    assert observation.values[_feature_index("ally_distance")] == 1.0
    assert observation.values[_feature_index("enemy1_alive")] == 0.0
    assert observation.values[_feature_index("enemy1_distance")] == 1.0
    assert observation.values[_feature_index("enemy2_alive")] == 0.0
    assert observation.values[_feature_index("enemy2_distance")] == 1.0


def test_2v2_ally_and_enemy_slots_are_populated() -> None:
    observation = ObservationBuilder().build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("ally_alive")] == 1.0
    assert observation.values[_feature_index("ally_role_tank")] == 1.0
    assert observation.values[_feature_index("enemy1_alive")] == 1.0
    assert observation.values[_feature_index("enemy2_alive")] == 1.0


def test_dead_agents_represented_consistently() -> None:
    state = make_state()
    eliminate(state.agents["team1_ranged_dps_0"])

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("enemy1_alive")] == 1.0
    assert observation.values[_feature_index("enemy1_role_tank")] == 1.0
    assert observation.values[_feature_index("enemy2_alive")] == 0.0
    assert observation.values[_feature_index("enemy2_hp_norm")] == 0.0


def test_dead_ally_encoding_is_stable() -> None:
    state = make_state()
    eliminate(state.agents["team0_tank_0"])

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("ally_alive")] == 0.0
    assert observation.values[_feature_index("ally_hp_norm")] == 0.0
    assert observation.values[_feature_index("ally_role_tank")] == 1.0


def test_ally_threat_indicator_uses_enemy_attack_range() -> None:
    state = make_state()
    ally = state.agents["team0_tank_0"]
    enemy = state.agents["team1_tank_0"]
    enemy.position = (ally.position[0] + enemy.attack_range * 0.5, ally.position[1])

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("ally_threat_indicator")] == 1.0


def test_enemy_in_attack_range_uses_controlled_basic_attack_range() -> None:
    state = make_state()
    controlled = state.agents[CONTROLLED_AGENT_ID]
    enemy = state.agents["team1_ranged_dps_0"]
    enemy.position = (
        controlled.position[0] + controlled.attack_range * 0.5,
        controlled.position[1],
    )

    observation = ObservationBuilder().build_observation(state, CONTROLLED_AGENT_ID)

    assert observation.values[_feature_index("enemy1_in_attack_range")] == 1.0


def test_repeated_calls_produce_same_feature_name_order() -> None:
    builder = ObservationBuilder()
    first = builder.build_observation(make_state(), CONTROLLED_AGENT_ID)
    second = builder.build_observation(make_state(), CONTROLLED_AGENT_ID)

    assert first.feature_names == second.feature_names
