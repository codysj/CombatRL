import numpy as np
from tests.unit.agent_test_helpers import eliminate, make_state, movement_actions

from combatrl.envs.action_codec import ACTION_ID_TO_TYPE, ActionCodec
from combatrl.schemas.actions import ActionType


def test_n_actions_matches_mapping() -> None:
    codec = ActionCodec()

    assert codec.n_actions() == len(ACTION_ID_TO_TYPE)


def test_decode_valid_action_id() -> None:
    codec = ActionCodec()

    command = codec.decode(1, "team0_ranged_dps_0")

    assert command.agent_id == "team0_ranged_dps_0"
    assert command.action_type == ActionType.MOVE_UP


def test_invalid_action_id_falls_back_to_no_op() -> None:
    codec = ActionCodec()

    command = codec.decode(999, "team0_ranged_dps_0")

    assert command.action_type == ActionType.NO_OP


def test_encode_decode_roundtrip_for_all_action_types() -> None:
    codec = ActionCodec()

    for action_type in ActionType:
        action_id = codec.encode(action_type)
        assert codec.decode(action_id, "team0_ranged_dps_0").action_type == action_type


def test_dead_agent_valid_mask_only_allows_no_op() -> None:
    state = make_state()
    codec = ActionCodec()
    eliminate(state.agents["team0_ranged_dps_0"])

    mask = codec.valid_action_mask(state, "team0_ranged_dps_0")

    assert np.flatnonzero(mask).tolist() == [codec.fallback_action_id()]


def test_attack_nearest_invalid_if_no_live_enemies() -> None:
    state = make_state()
    codec = ActionCodec()
    for agent in state.agents.values():
        if agent.team_id == 1:
            eliminate(agent)

    mask = codec.valid_action_mask(state, "team0_ranged_dps_0")

    assert mask[codec.encode(ActionType.ATTACK_NEAREST)] == 0
    for action_type in movement_actions():
        assert mask[codec.encode(action_type)] == 1


def test_attack_nearest_valid_if_any_live_enemy_exists_in_2v2() -> None:
    state = make_state()
    codec = ActionCodec()

    mask = codec.valid_action_mask(state, "team0_ranged_dps_0")

    assert mask[codec.encode(ActionType.ATTACK_NEAREST)] == 1
