from pathlib import Path

import numpy as np

from combatrl.envs import CombatRLGymEnv

ENV_CONFIG_PATH = Path("configs/env/gym_2v2_controlled_ranged.yaml")


def test_2v2_random_rollouts_do_not_crash_and_end_cleanly() -> None:
    env = CombatRLGymEnv(ENV_CONFIG_PATH)
    rng = np.random.default_rng(42)
    try:
        for episode in range(5):
            observation, _ = env.reset(seed=42 + episode)
            terminated = False
            truncated = False
            info = {}
            for _ in range(350):
                assert np.isfinite(observation).all()
                action = int(rng.integers(0, env.action_space.n))
                observation, _, terminated, truncated, info = env.step(action)
                if terminated or truncated:
                    break

            assert terminated or truncated
            assert info["terminal_reason"] in {"elimination", "max_ticks"}
    finally:
        env.close()
