import importlib.util
from pathlib import Path

import numpy as np

from combatrl.envs import ActionCodec, CombatRLGymEnv

ENV_CONFIG_PATH = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def test_env_instantiates_with_expected_spaces() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        assert env.observation_space.shape == (49,)
        assert env.action_space.n == ActionCodec().n_actions()
    finally:
        env.close()


def test_reset_returns_numpy_observation_and_info() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        observation, info = env.reset(seed=42)
    finally:
        env.close()

    assert isinstance(observation, np.ndarray)
    assert observation.dtype == np.float32
    assert info["match_id"] == "mvp_2v2_elimination_seed_42"
    assert info["seed"] == 42
    assert info["controlled_agent_id"] == "team0_ranged_dps_0"
    assert info["scenario_id"] == "mvp_2v2_elimination"


def test_reset_same_seed_gives_identical_observation() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        first, _ = env.reset(seed=42)
        second, _ = env.reset(seed=42)
    finally:
        env.close()

    np.testing.assert_array_equal(first, second)


def test_step_returns_gymnasium_contract_values() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        env.reset(seed=42)
        observation, reward, terminated, truncated, info = env.step(0)
    finally:
        env.close()

    assert isinstance(observation, np.ndarray)
    assert observation.dtype == np.float32
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)
    assert np.isfinite(observation).all()


def test_invalid_action_does_not_crash_and_applies_penalty() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    try:
        env.reset(seed=42)
        _, reward, _, _, info = env.step(999)
    finally:
        env.close()

    assert reward < 0.0
    assert info["invalid_action"] is True
    assert info["reward_breakdown"]["components"]["invalid_action_penalty"] == -0.02


def test_max_ticks_sets_truncated_not_terminated() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    env.simulation_config = env.simulation_config.model_copy(update={"max_ticks": 4})
    try:
        env.reset(seed=42)
        _, _, terminated, truncated, info = env.step(0)
    finally:
        env.close()

    assert terminated is False
    assert truncated is True
    assert info["terminal_reason"] == "max_ticks"


def test_step_after_done_requires_reset() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    env.simulation_config = env.simulation_config.model_copy(update={"max_ticks": 4})
    try:
        env.reset(seed=42)
        env.step(0)
        try:
            env.step(0)
        except RuntimeError as exc:
            assert "call reset" in str(exc)
        else:
            raise AssertionError("step after done should raise RuntimeError")
    finally:
        env.close()


def test_close_is_safe() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    env.reset(seed=42)

    env.close()
    env.close()


def test_optional_sb3_dummy_vec_env_instantiates_when_installed() -> None:
    if importlib.util.find_spec("stable_baselines3") is None:
        return
    from stable_baselines3.common.vec_env import DummyVecEnv

    vec_env = DummyVecEnv([lambda: CombatRLGymEnv(ENV_CONFIG_PATH)])
    try:
        observation = vec_env.reset()
    finally:
        vec_env.close()

    assert observation.shape[-1] == 49
