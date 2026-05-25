from tests.unit.agent_test_helpers import eliminate, make_state

from combatrl.agents.utility import (
    direction_action_away,
    direction_action_toward,
    get_live_allies,
    get_live_enemies,
    get_lowest_hp_enemy,
    get_nearest_enemy,
)
from combatrl.schemas.actions import ActionType


def test_nearest_enemy_selection_is_deterministic() -> None:
    state = make_state()
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team1_tank_0"].position = (20.0, 10.0)
    state.agents["team1_ranged_dps_0"].position = (20.0, 10.0)

    assert get_nearest_enemy(state, "team0_tank_0").agent_id == "team1_ranged_dps_0"


def test_lowest_hp_enemy_tie_breaks_by_agent_id() -> None:
    state = make_state()
    state.agents["team1_tank_0"].hp = 20.0
    state.agents["team1_ranged_dps_0"].hp = 20.0

    assert get_lowest_hp_enemy(state, "team0_tank_0").agent_id == "team1_ranged_dps_0"


def test_dead_enemies_are_ignored() -> None:
    state = make_state()
    eliminate(state.agents["team1_ranged_dps_0"])
    state.agents["team1_ranged_dps_0"].position = (11.0, 10.0)
    state.agents["team1_tank_0"].position = (40.0, 10.0)

    assert get_nearest_enemy(state, "team0_tank_0").agent_id == "team1_tank_0"
    assert [enemy.agent_id for enemy in get_live_enemies(state, "team0_tank_0")] == ["team1_tank_0"]


def test_dead_allies_are_ignored() -> None:
    state = make_state()
    eliminate(state.agents["team0_ranged_dps_0"])

    assert get_live_allies(state, "team0_tank_0") == []


def test_direction_action_toward_returns_expected_diagonal_action() -> None:
    assert direction_action_toward((0.0, 0.0), (1.0, -1.0)) == ActionType.MOVE_UP_RIGHT


def test_direction_action_away_returns_opposite_direction() -> None:
    assert direction_action_away((0.0, 0.0), (1.0, -1.0)) == ActionType.MOVE_DOWN_LEFT


def test_selection_does_not_depend_on_dict_insertion_order() -> None:
    state = make_state()
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team1_tank_0"].position = (20.0, 10.0)
    state.agents["team1_ranged_dps_0"].position = (20.0, 10.0)
    state.agents = {
        "team1_tank_0": state.agents["team1_tank_0"],
        "team0_tank_0": state.agents["team0_tank_0"],
        "team1_ranged_dps_0": state.agents["team1_ranged_dps_0"],
        "team0_ranged_dps_0": state.agents["team0_ranged_dps_0"],
    }

    assert get_nearest_enemy(state, "team0_tank_0").agent_id == "team1_ranged_dps_0"
