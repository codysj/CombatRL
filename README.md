# CombatRL

CombatRL is a deterministic, headless-first tactical arena simulation project for
studying reinforcement learning, multi-agent behavior, replay analytics, and
behavior-profile control. The simulator is intentionally built around stable
schemas and replay-first debugging so later systems can be tested independently.

## Phase Status

Phase P10 adds natural-language-to-profile parsing on top of the stable 2v2
team-aware environment and behavior-profile system. The project can load the default MVP config, initialize a 2v2
match, run bot-vs-bot matches to elimination or timeout, save replay artifacts,
validate them, render saved frames without recomputing simulation logic, run
headless 2v2 rollouts through `CombatRLGymEnv`, train PPO smoke baselines for
1v1 or 2v2 configs, save SB3 checkpoints, evaluate checkpoints, and generate
sample replay artifacts from evaluated policies. It can also load bounded
numeric behavior profiles and compare heuristic, profiled, random, and PPO
policies across fixed seeds with JSON, CSV, JSONL, Markdown, and sample replay
artifacts. Natural-language commands can now be translated into validated
`BehaviorProfile` objects and compared through the existing evaluation stack.

Objective control, pathfinding, frontend, backend, PettingZoo, self-play,
opponent pools, and advanced MARL systems are intentionally not implemented yet.

## Simulator Model

Actions are discrete `ActionCommand` values:

- `NO_OP`
- cardinal and diagonal movement actions
- `ATTACK_NEAREST`

Movement uses fixed timestep logic:

```text
new_position = old_position + normalized_direction * movement_speed * dt
dt = 1.0 / tick_rate_hz
```

Diagonal movement is normalized, positions clamp to the arena, and dead agents
cannot move or attack. Combat is intentionally minimal: `ATTACK_NEAREST` selects
the nearest alive enemy in range, resolves ties by sorted `agent_id`, applies
instant damage, clamps HP at zero, and sets attack cooldown on successful hits.

Per tick, the simulator executes:

1. Validate actions.
2. Resolve movement.
3. Resolve attacks.
4. Apply deaths.
5. Decrement cooldowns.
6. Evaluate terminal state.
7. Increment tick.
8. Validate invariants.

## Setup

Install dependencies:

```powershell
uv sync --extra dev
```

Install the optional renderer:

```powershell
uv sync --extra dev --extra renderer
```

Run tests:

```powershell
uv run pytest
```

Run linting:

```powershell
uv run ruff check .
uv run ruff format --check .
```

Run the headless match script:

```powershell
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --seed 42
```

Run the Gymnasium environment check:

```powershell
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 5 --seed 42
```

Run a short PPO smoke train:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml --smoke
uv run python scripts/train_ppo.py --config configs/training/ppo_2v2_baseline.yaml --smoke
```

Evaluate a checkpoint:

```powershell
uv run python scripts/evaluate_checkpoint.py <run_dir>/model_final.zip --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 5 --seed-start 1000
```

Run and save a replay:

```powershell
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --seed 42 --save-replay
```

Expected summary fields include:

- `scenario_id: mvp_2v2_elimination`
- `team0_policy`
- `team1_policy`
- `agent_count: 4`
- `final_tick`
- `terminal: true`
- `terminal_reason: elimination` or `terminal_reason: timeout`
- `winner_team_id`
- `replay_path` when `--save-replay` is used
- `replay_frame_count` when `--save-replay` is used
- `replay_event_count` when `--save-replay` is used

## Heuristic Baseline Agents

Available policy IDs:

- `random`: seeded uniform random simple actions.
- `aggressive`: closes on the lowest-HP live enemy and attacks when ready.
- `defensive`: retreats when low HP or pressured, regroups with allies, and
  attacks only from safer positions.
- `kiter`: tries to stay near attack range and backs up when enemies are too
  close.
- `protector`: stays near vulnerable allies and attacks enemies threatening
  them.
- `profiled:<profile>`: wraps the aggressive base policy with a behavior
  profile.
- `profiled:<base_policy>:<profile>`: wraps a selected base policy with a
  behavior profile.

Run bot matchups:

```powershell
uv run python scripts/run_match.py --team0-policy kiter --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy protector --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy profiled:defensive --team1-policy aggressive --seed 42 --save-replay
```

Optional role overrides:

```powershell
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --team0-tank-policy protector --team0-ranged-policy kiter --seed 42
```

## Behavior Profiles

Manual profile presets live under `configs/profiles/`: `balanced`,
`aggressive`, `defensive`, `kiter`, and `protective`. A profile is a numeric
control object with bounded axes for aggression, caution, cohesion,
protectiveness, focus fire, greed, spacing, and reserved objective bias.
Profiles rerank existing valid action candidates at inference time; they do not
retrain policies, change simulator rules, mutate simulator state, output raw
actions, or change observation shape.

List profiles:

```powershell
uv run python -c "from combatrl.profiles.loader import list_profiles; print(list_profiles())"
```

Run a comparison:

```powershell
uv run python scripts/compare_profiles.py --profiles aggressive defensive protective kiter balanced --base-policy aggressive --num-seeds 10 --save-replays
```

The comparison now uses the P9 evaluation framework. It writes per-profile P9
evaluation artifacts, JSON and CSV profile summaries, a Markdown comparison
report, and one sample replay per profile when `--save-replays` is enabled.
Expected coarse signals are higher attack rate for aggressive, higher retreat
rate for defensive, lower ally distance for protective, and greater enemy
spacing for kiter.

## NLP Command Parser

P10 maps natural language to the existing `BehaviorProfile` schema. The NLP
layer is a translator, not a controller: it never calls `env.step`, emits raw
action IDs, mutates simulator state, executes code, or invents unsupported
profile fields.

Parse commands:

```powershell
uv run python scripts/parse_command.py "play aggressively"
uv run python scripts/parse_command.py "protect ally and stay together"
uv run python scripts/parse_command.py "kite backward and avoid close combat"
uv run python scripts/parse_command.py "teleport behind them and buy items"
```

Save a parsed profile:

```powershell
uv run python scripts/parse_command.py "protect ally" --output-profile artifacts/profiles/protect_ally.yaml
```

Run command-driven comparisons:

```powershell
uv run python scripts/compare_command_profiles.py --commands "play aggressively" "protect ally" "kite backward" --num-seeds 3 --save-replays
```

The parser has deterministic rule mode plus an optional structured-output LLM
interface that accepts an injected callable. Tests use fake callables only; no
network access or API key is required. Unsupported requests such as teleporting,
items, fog, wards, ultimates, healing, revives, summons, building, or unsupported
spells are reported explicitly in `unsupported_requests`.

## Evaluation Framework

Evaluation artifacts are local files under:

```text
artifacts/metrics/evaluations/<evaluation_id>/
```

Each run writes `evaluation_result.json`, `per_match_metrics.csv`,
`per_match_metrics.jsonl`, `evaluation_report.md`, and optional replay samples.
Metrics are computed from replay frames/events where possible and include match
outcome, damage, survival, spacing, attack/retreat/no-op rates, ally distance,
cohesion, and best-effort teamwork metrics.

Run a tiny heuristic evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type heuristic --policy-id aggressive --seed-start 100 --num-seeds 3 --save-replays --replay-sample-count 1
```

Run a profile evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type profiled --base-policy aggressive --profile defensive --seed-start 100 --num-seeds 30 --save-replays
```

Run a PPO checkpoint evaluation:

```powershell
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type ppo_checkpoint --checkpoint <checkpoint_path> --seed-start 1000 --num-seeds 30
```

Do not make strong claims from fewer than 20 matches. Prefer at least 30 seeds
for MVP comparisons, and inspect representative replay samples before drawing
conclusions.

## Gymnasium Environment

Default env config:

```text
configs/env/gym_2v2_controlled_ranged.yaml
```

The wrapper controls `team0_ranged_dps_0`, runs a scripted `protector`
teammate, and uses `aggressive` plus `random` scripted opponents by default.
Gymnasium is only a wrapper: simulator state transitions and win conditions remain in
`SimulationEngine`.

Spaces:

- `observation_space`: `Box(low=-1.0, high=1.0, shape=(49,), dtype=np.float32)`
- `action_space`: `Discrete(10)`

Actions:

- `0`: `NO_OP`
- `1`: `MOVE_UP`
- `2`: `MOVE_DOWN`
- `3`: `MOVE_LEFT`
- `4`: `MOVE_RIGHT`
- `5`: `MOVE_UP_LEFT`
- `6`: `MOVE_UP_RIGHT`
- `7`: `MOVE_DOWN_LEFT`
- `8`: `MOVE_DOWN_RIGHT`
- `9`: `ATTACK_NEAREST`

The 49-feature observation layout contains self features, one ally slot, two
enemy slots, arena features, and simple tactical features. Rewards expose a
breakdown with win/loss, damage dealt, damage taken, death, ally death, invalid
action, and time components.

Run one 2v2 env episode and save a replay:

```powershell
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
uv run python scripts/validate_replay.py <replay_path>
```

Basic usage:

```python
from combatrl.envs import CombatRLGymEnv

env = CombatRLGymEnv("configs/env/gym_2v2_controlled_ranged.yaml")
observation, info = env.reset(seed=42)
observation, reward, terminated, truncated, info = env.step(0)
env.close()
```

See `docs/rl_environment.md` and `docs/phase_p5.md` for the full contract.

## PPO Training

Default training config:

```text
configs/training/ppo_1v1_baseline.yaml
configs/training/ppo_2v2_baseline.yaml
```

The first baseline uses Stable-Baselines3 PPO with `MlpPolicy`, `DummyVecEnv`,
separate train/evaluation envs, unique vector-env seeds, CPU execution, SB3
checkpoint callbacks, and local JSON/CSV artifacts. Training is headless and
does not import renderer, browser, FastAPI, frontend, or Pygame code.

Artifacts are saved under:

```text
artifacts/checkpoints/ppo_1v1_baseline/run_<timestamp>/
```

Important files:

- `model_final.zip`: final SB3 checkpoint.
- `best_model.zip`: best EvalCallback checkpoint when an evaluation fires.
- `config.yaml`: resolved training config copy.
- `model_metadata.json`: local checkpoint registry metadata.
- `metrics.json`: training run summary.
- `evaluation_metrics.json`: checkpoint evaluation metrics.
- `eval_history.csv`: converted callback evaluation history when available.
- `sample_replays/`: optional evaluated-policy replay artifacts.

Run a longer local experiment:

```powershell
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml
```

Generate a sample replay during evaluation:

```powershell
uv run python scripts/evaluate_checkpoint.py <checkpoint> --env-config configs/env/gym_1v1_ranged_vs_random.yaml --episodes 1 --save-replay
uv run python scripts/validate_replay.py <sample_replay_path>
```

The smoke run only proves that PPO, checkpointing, evaluation, metadata, and
replay capture work. The "beats random" learning criterion is a manual longer
run target: increase timesteps gradually, inspect replays, then compare against
the random baseline before trusting reward curves.

## Replays

Replay files are written under:

```text
artifacts/replays/<timestamp>_<scenario_id>_seed-<seed>/
```

Each replay contains:

- `metadata.json`
- `frames.jsonl`
- `events.jsonl`
- `summary.json`

Validate a replay:

```powershell
uv run python scripts/validate_replay.py artifacts/replays/<replay-dir>
```

Render a replay:

```powershell
uv run python scripts/render_replay.py artifacts/replays/<replay-dir>
```

Renderer controls:

- `Space`: pause/play
- `Right arrow`: step forward while paused
- `Left arrow`: step backward while paused
- `1`, `2`, `4`: speed controls
- `Esc` or window close: quit

See `docs/replay_schema.md` and `docs/phase_p3.md` for schema details and
completion notes.

## Manual Verification

Run:

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run python scripts/parse_command.py "play aggressively"
uv run python scripts/parse_command.py "protect ally"
uv run python scripts/parse_command.py "teleport and buy items"
uv run python scripts/compare_command_profiles.py --commands "play aggressively" "kite backward" --num-seeds 2 --save-replays
uv run python scripts/train_ppo.py --config configs/training/ppo_1v1_baseline.yaml --smoke
uv run python scripts/train_ppo.py --config configs/training/ppo_2v2_baseline.yaml --smoke
uv run python scripts/check_env.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --episodes 3 --seed 42
uv run python scripts/run_2v2_env_episode.py --env-config configs/env/gym_2v2_controlled_ranged.yaml --seed 42 --policy random --save-replay
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --seed 42 --save-replay
uv run python scripts/evaluate_policy.py --scenario configs/env/gym_2v2_controlled_ranged.yaml --policy-type heuristic --policy-id aggressive --seed-start 100 --num-seeds 3 --save-replays --replay-sample-count 1
```

Validate the printed replay path:

```powershell
uv run python scripts/validate_replay.py <replay_path>
uv run python scripts/render_replay.py <replay_path>
```

Confirm visually that aggressive agents close distance and attack, defensive
agents retreat when pressured or low HP, HP bars change from attacks, and the
match terminates by elimination or timeout. Then run:

```powershell
uv run python scripts/run_match.py --team0-policy kiter --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy protector --team1-policy aggressive --seed 42 --save-replay
```

Confirm visually that kiter agents try to maintain spacing and protector agents
stay closer to allies than the aggressive baseline. Run the same command twice
with the same seed and confirm summary and replay content are deterministic,
ignoring timestamps and output directory.

See `docs/agents.md`, `docs/phase_p3.md`, `docs/phase_p4.md`,
`docs/phase_p5.md`, `docs/phase_p6.md`, `docs/rl_environment.md`, and
`docs/phase_p7.md`, `docs/phase_p8.md`, `docs/profiles.md`,
`docs/phase_p9.md`, `docs/evaluation.md`, `docs/nlp.md`,
`docs/phase_p10.md`, `docs/rl_environment.md`, and `docs/rl_training.md` for
details.

Next phase: P11 Backend and Frontend Dashboard.
