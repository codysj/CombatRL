# Phase P5 Completion Notes

Phase P5 adds a Gymnasium-compatible, headless single-agent RL wrapper around
the deterministic CombatRL simulator.

## Implemented

- `EnvironmentConfig` in `combatrl.schemas.configs`.
- `ObservationVector` in `combatrl.schemas.observations`.
- `RewardBreakdown` in `combatrl.schemas.rewards`.
- `ActionCodec` with the 10-action MVP discrete mapping.
- `ObservationBuilder` with a fixed 49-feature numeric vector.
- `RewardBuilder` with required MVP reward components.
- `CombatRLGymEnv` with Gymnasium reset/step signatures.
- Default env config: `configs/env/gym_2v2_controlled_ranged.yaml`.
- Headless check script: `scripts/check_env.py`.
- Unit and integration tests for observations, rewards, action masks, API
  contract, deterministic reset, invalid actions, truncation, and random
  rollouts.

## Contract

`CombatRLGymEnv` wraps `SimulationEngine`. It does not move movement, combat,
cooldown, death, or win-condition logic into the RL layer.

Spaces:

- `Box(low=-1.0, high=1.0, shape=(49,), dtype=np.float32)`
- `Discrete(10)`

Gymnasium signatures:

- `reset(seed=...) -> observation, info`
- `step(action) -> observation, reward, terminated, truncated, info`

The wrapper runs with `render_mode=None` by default and does not require Pygame.

## Deferred

- PPO training loop.
- Stable-Baselines3 training scripts.
- Checkpoints.
- Evaluation framework.
- Behavior profiles.
- NLP.
- Frontend/backend.
- PettingZoo and advanced MARL.
- Support/healer mechanics.
- Objective-control mode.
- Reward overengineering.

Recommended next phase: P6 PPO Training Baseline.
