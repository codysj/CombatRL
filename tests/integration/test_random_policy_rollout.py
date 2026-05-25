from pathlib import Path

import numpy as np

from combatrl.envs import CombatRLGymEnv

ENV_CONFIG_PATH = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def test_random_rollout_equivalent_steps_do_not_crash_or_nan() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    rng = np.random.default_rng(123)
    steps_run = 0
    try:
        observation, _ = env.reset(seed=123)
        for episode in range(20):
            if episode > 0:
                observation, _ = env.reset(seed=123 + episode)
            for _ in range(50):
                assert np.isfinite(observation).all()
                action = int(rng.integers(0, env.action_space.n))
                observation, _, terminated, truncated, _ = env.step(action)
                steps_run += 1
                assert np.isfinite(observation).all()
                if terminated or truncated:
                    break
    finally:
        env.close()

    assert steps_run >= 100
