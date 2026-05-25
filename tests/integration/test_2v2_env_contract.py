from pathlib import Path

import numpy as np
import pytest

from combatrl.envs import CombatRLGymEnv
from combatrl.schemas.configs import load_environment_config

ENV_CONFIG_PATH = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def test_2v2_env_instantiates_and_resolves_scripted_policies() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        observation, info = env.reset(seed=42)
    finally:
        env.close()

    assert observation.shape == (49,)
    assert info["controlled_agent_id"] == "team0_ranged_dps_0"
    assert info["controlled_team_id"] == 0
    assert info["ally_agent_ids"] == ["team0_tank_0"]
    assert info["enemy_agent_ids"] == ["team1_ranged_dps_0", "team1_tank_0"]


def test_explicit_scripted_policy_by_agent_id_is_supported() -> None:
    config = load_environment_config(ENV_CONFIG_PATH).model_copy(
        update={
            "scripted_policy_by_agent_id": {
                "team0_tank_0": "protector",
                "team1_tank_0": "aggressive",
                "team1_ranged_dps_0": "random",
            }
        }
    )
    env = CombatRLGymEnv(config)
    try:
        env.reset(seed=42)
        policy_ids = {
            agent_id: policy.policy_id for agent_id, policy in env._policy_by_agent_id.items()
        }
        assert policy_ids == {
            "team0_tank_0": "protector",
            "team1_ranged_dps_0": "random",
            "team1_tank_0": "aggressive",
        }
    finally:
        env.close()


def test_missing_explicit_scripted_policy_fails_validation() -> None:
    config = load_environment_config(ENV_CONFIG_PATH).model_copy(
        update={"scripted_policy_by_agent_id": {"team0_tank_0": "protector"}}
    )

    with pytest.raises(ValueError, match="assign every non-controlled"):
        CombatRLGymEnv(config)


def test_step_info_contains_2v2_team_fields_and_action_mask() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        env.reset(seed=42)
        _, _, _, _, info = env.step(0)
    finally:
        env.close()

    assert info["team0_alive"] >= 0
    assert info["team1_alive"] >= 0
    assert isinstance(info["controlled_agent_alive"], bool)
    assert info["ally_alive_count"] in {0, 1}
    assert info["enemy_alive_count"] in {0, 1, 2}
    assert info["action_mask"].shape == (env.action_space.n,)
    assert info["events_count"] >= 0


def test_reset_same_seed_and_actions_give_same_final_summary() -> None:
    actions = [0, 9, 1, 9, 4, 9, 0, 0, 9, 2]
    first = _run_fixed_actions(actions)
    second = _run_fixed_actions(actions)

    assert first == second


def test_controlled_death_does_not_crash_when_not_terminal_on_controlled_death() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        env.reset(seed=42)
        assert env._engine is not None
        controlled = env._engine.state.agents[env.env_config.controlled_agent_id]
        controlled.hp = 0.0
        controlled.alive = False
        _, _, terminated, truncated, info = env.step(9)
    finally:
        env.close()

    assert terminated is False
    assert truncated is False
    assert info["controlled_agent_alive"] is False
    assert np.flatnonzero(info["action_mask"]).tolist() == [env.action_codec.fallback_action_id()]


def _run_fixed_actions(actions: list[int]) -> dict[str, object]:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        env.reset(seed=77)
        info: dict[str, object] = {}
        for action in actions:
            _, _, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        return {
            "tick": info["tick"],
            "team0_alive": info["team0_alive"],
            "team1_alive": info["team1_alive"],
            "controlled_alive": info["controlled_agent_alive"],
            "winner_team_id": info["winner_team_id"],
        }
    finally:
        env.close()
