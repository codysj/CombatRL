from tests.integration.bot_match_helpers import run_bot_match
from tests.unit.agent_test_helpers import make_engine

from combatrl.agents.aggressive_bot import AggressiveBot
from combatrl.agents.defensive_bot import DefensiveBot
from combatrl.agents.kiter_bot import KiterBot
from combatrl.agents.protector_bot import ProtectorBot
from combatrl.core.geometry import distance
from combatrl.schemas.actions import ActionType


def test_random_vs_random_match_completes_without_crashing() -> None:
    engine, _ = run_bot_match(team0_policy_id="random", team1_policy_id="random", max_ticks=80)

    assert engine.state.terminal is True


def test_aggressive_vs_defensive_match_completes_without_crashing() -> None:
    engine, _ = run_bot_match(
        team0_policy_id="aggressive",
        team1_policy_id="defensive",
        max_ticks=240,
    )

    assert engine.state.terminal is True


def test_kiter_vs_aggressive_match_completes_without_crashing() -> None:
    engine, _ = run_bot_match(
        team0_policy_id="kiter",
        team1_policy_id="aggressive",
        max_ticks=240,
    )

    assert engine.state.terminal is True


def test_protector_setup_completes_without_crashing() -> None:
    engine, _ = run_bot_match(
        team0_policy_id="protector",
        team1_policy_id="aggressive",
        max_ticks=240,
    )

    assert engine.state.terminal is True


def test_same_seed_and_policies_produce_identical_final_state() -> None:
    engine_a, _ = run_bot_match(
        team0_policy_id="aggressive",
        team1_policy_id="defensive",
        seed=77,
        max_ticks=160,
    )
    engine_b, _ = run_bot_match(
        team0_policy_id="aggressive",
        team1_policy_id="defensive",
        seed=77,
        max_ticks=160,
    )

    assert engine_a.state.model_dump(mode="json") == engine_b.state.model_dump(mode="json")


def test_aggressive_has_at_least_as_many_attack_attempts_as_defensive_in_controlled_setup() -> None:
    engine = make_engine(max_ticks=20)
    state = engine.state
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team1_tank_0"].position = (15.0, 10.0)
    state.agents["team1_tank_0"].hp = 50.0
    state.agents["team0_ranged_dps_0"].position = (10.0, 20.0)
    state.agents["team1_ranged_dps_0"].position = (15.0, 20.0)
    aggressive_action = AggressiveBot().select_action(state, "team0_tank_0")
    defensive_action = DefensiveBot().select_action(state, "team1_tank_0")

    assert aggressive_action.action_type == ActionType.ATTACK_NEAREST
    assert defensive_action.action_type != ActionType.ATTACK_NEAREST


def test_defensive_emits_retreat_action_when_low_hp() -> None:
    state = make_engine().state
    state.agents["team0_tank_0"].position = (20.0, 10.0)
    state.agents["team0_tank_0"].hp = 20.0
    state.agents["team1_tank_0"].position = (24.0, 10.0)

    assert DefensiveBot().select_action(state, "team0_tank_0").action_type == ActionType.MOVE_LEFT


def test_kiter_increases_or_maintains_distance_when_enemy_is_too_close() -> None:
    engine = make_engine()
    state = engine.state
    state.agents["team0_ranged_dps_0"].position = (20.0, 10.0)
    state.agents["team1_tank_0"].position = (25.0, 10.0)
    before = distance(
        state.agents["team0_ranged_dps_0"].position,
        state.agents["team1_tank_0"].position,
    )

    action = KiterBot().select_action(state, "team0_ranged_dps_0")
    engine.step([action])
    after = distance(
        state.agents["team0_ranged_dps_0"].position,
        state.agents["team1_tank_0"].position,
    )

    assert after >= before


def test_protector_reduces_distance_to_threatened_ally() -> None:
    engine = make_engine()
    state = engine.state
    state.agents["team0_tank_0"].position = (10.0, 10.0)
    state.agents["team0_ranged_dps_0"].position = (30.0, 10.0)
    state.agents["team0_ranged_dps_0"].hp = 20.0
    state.agents["team1_tank_0"].position = (32.0, 10.0)
    before = distance(
        state.agents["team0_tank_0"].position,
        state.agents["team0_ranged_dps_0"].position,
    )

    action = ProtectorBot().select_action(state, "team0_tank_0")
    engine.step([action])
    after = distance(
        state.agents["team0_tank_0"].position,
        state.agents["team0_ranged_dps_0"].position,
    )

    assert after < before
