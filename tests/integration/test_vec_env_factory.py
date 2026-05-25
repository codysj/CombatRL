from pathlib import Path

import numpy as np

from combatrl.training.configs import load_training_config
from combatrl.training.vec_env import make_vec_envs

CONFIG_PATH = Path("configs/training/ppo_1v1_baseline.yaml")


def test_make_vec_envs_reset_step_and_close() -> None:
    config = load_training_config(CONFIG_PATH).model_copy(update={"n_envs": 2})
    vec_env = make_vec_envs(config)
    try:
        observation = vec_env.reset()
        assert vec_env.num_envs == 2
        assert observation.shape == (2, 49)
        assert np.isfinite(observation).all()

        actions = [vec_env.action_space.sample() for _ in range(vec_env.num_envs)]
        next_observation, rewards, dones, infos = vec_env.step(actions)

        assert next_observation.shape == (2, 49)
        assert rewards.shape == (2,)
        assert dones.shape == (2,)
        assert len(infos) == 2
        assert np.isfinite(next_observation).all()
        assert np.isfinite(rewards).all()
    finally:
        vec_env.close()
