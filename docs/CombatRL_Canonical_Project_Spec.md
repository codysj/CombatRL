# CombatRL Canonical Project Specification

**Document status:** Authoritative implementation specification  
**Project codename:** `CombatRL`  
**Document type:** Machine-optimized engineering contract for future LLM implementation sessions  
**Primary implementation mode:** Incremental autonomous development across multiple sessions  
**Last updated:** 2026-05-23  

---

## 1. Project Identity

### 1.1 Project Codename

`CombatRL`

### 1.2 High-Level Purpose

`CombatRL` is a deterministic, top-down, MOBA-style tactical arena simulation for studying reinforcement learning, multi-agent behavior, role-based combat, behavior-profile modulation, replay analytics, and natural-language tactical control.

The system is a controlled research and portfolio environment, not a commercial game. It must be built so that every major subsystem can be tested, replayed, visualized, and evaluated independently.

### 1.3 Primary Objectives

| Objective ID | Objective | Required for MVP | Required for Post-MVP | Required for Research Grade |
|---|---|---:|---:|---:|
| `OBJ-001` | Deterministic 2D tactical combat simulator | Yes | Yes | Yes |
| `OBJ-002` | Headless simulation suitable for RL rollouts | Yes | Yes | Yes |
| `OBJ-003` | Structured observations and discrete tactical actions | Yes | Yes | Yes |
| `OBJ-004` | Heuristic baseline agents | Yes | Yes | Yes |
| `OBJ-005` | Replay logging and replay playback | Yes | Yes | Yes |
| `OBJ-006` | Gymnasium-compatible single-agent wrapper | Yes | Yes | Yes |
| `OBJ-007` | First PPO-trained policy beating weak baselines | Yes | Yes | Yes |
| `OBJ-008` | 2v2 tactical arena with role-aware agents | Yes | Yes | Yes |
| `OBJ-009` | Behavior-profile control system | Yes | Yes | Yes |
| `OBJ-010` | Metrics and evaluation framework | Yes | Yes | Yes |
| `OBJ-011` | Natural-language-to-profile parser | No | Yes | Yes |
| `OBJ-012` | Frontend replay viewer and dashboard | No | Yes | Yes |
| `OBJ-013` | Support/healer role | No | Yes | Yes |
| `OBJ-014` | Objective-control game mode | No | Yes | Yes |
| `OBJ-015` | Self-play, opponent pools, advanced MARL | No | No | Yes |

### 1.4 MVP Definition

The MVP is complete when the repository can run the following end-to-end workflow:

1. Start a deterministic 2v2 arena match.
2. Use two initial roles: `tank` and `ranged_dps`.
3. Run matches between heuristic agents.
4. Save match replay files.
5. Render replay playback with debug overlays.
6. Train a basic PPO policy in a Gymnasium wrapper against scripted opponents.
7. Evaluate the trained policy against random and heuristic baselines.
8. Apply manually defined behavior profiles such as `aggressive`, `defensive`, `kiter`, and `protective`.
9. Show that behavior profiles cause visible and measurable behavior differences.
10. Produce evaluation metrics for win rate, damage, survival, spacing, retreat frequency, and ally distance.

### 1.5 Post-MVP Definition

Post-MVP is complete when the system additionally supports:

1. Natural-language commands parsed into validated behavior profiles.
2. A browser-based replay viewer and metrics dashboard.
3. Support/healer role.
4. Objective-control mode using a central capture zone.
5. Side-by-side replay and profile comparisons.
6. Saved experiment runs with persistent metrics and model checkpoints.

### 1.6 Advanced / Research-Oriented Definition

Research-grade completion requires:

1. Multi-agent training beyond single controlled agent wrappers.
2. Role-specific policies and shared-policy experiments.
3. Self-play against checkpoint pools.
4. Curriculum learning scenarios.
5. Policy routing or behavior-conditioned policies.
6. Tournament-style evaluation suites.
7. Optional PettingZoo parallel environment API.
8. Optional RLlib integration for scalable MARL.

### 1.7 Non-Goals

The system is **not**:

| Non-Goal | Explanation |
|---|---|
| Full MOBA clone | No lanes, items, minions, towers, or Nexus in MVP. |
| Commercial game engine | Graphics are subordinate to reproducibility and observability. |
| Pixel-based RL benchmark | Observations are structured vectors, not raw image frames. |
| Real-time twitch game | Agent decisions are low-frequency tactical decisions, not 60 Hz mechanical inputs. |
| LLM-controlled action loop | Language never directly selects actions at runtime. It only produces validated behavior profiles. |
| Distributed RL platform in MVP | Training starts on a single machine with vectorized environments. |

### 1.8 Architectural Philosophy

All implementation must follow these principles:

1. **Simulator owns truth.** Game state and combat rules live only in the simulation core.
2. **Renderer is read-only.** Rendering consumes replay/state snapshots and never mutates game logic.
3. **Replay-first debugging.** Every match can be saved and replayed deterministically.
4. **Headless-first training.** RL training never depends on renderer availability.
5. **Interfaces before features.** Public contracts are defined before adding advanced mechanics.
6. **Vertical slices.** Each phase produces runnable, testable, visible behavior.
7. **Heuristics before RL.** Scripted agents validate the environment before learning begins.
8. **Manual profiles before NLP.** Behavior control must work before language parsing is introduced.

### 1.9 Development Philosophy

Future implementers must optimize for:

- deterministic behavior,
- fast iteration,
- visible debugging,
- small independently testable modules,
- stable public data models,
- minimal hidden state,
- reproducible experiments,
- graceful degradation when optional systems are absent.

### 1.10 Execution Philosophy

Future LLM coding sessions must:

1. Identify the current build phase.
2. Load the relevant phase section and subsystem contract.
3. Implement only the required interfaces for the current phase.
4. Add tests before expanding behavior complexity.
5. Run deterministic replay checks after simulation changes.
6. Avoid architectural drift from this specification.
7. Update this specification if public interfaces change.

---

## 2. Global Engineering Constraints

### 2.1 Deterministic Simulation Constraint

All simulation behavior must be deterministic under fixed inputs.

| Rule ID | Rule |
|---|---|
| `DET-001` | Every match must accept an explicit integer seed. |
| `DET-002` | All randomness must flow through a seeded project RNG wrapper. |
| `DET-003` | No simulation module may call global random functions directly. |
| `DET-004` | Entity update ordering must be stable and documented. |
| `DET-005` | Floating-point operations must avoid dependence on iteration over unordered containers. |
| `DET-006` | Replaying the same action sequence with the same seed must produce identical terminal state. |

### 2.2 Replay Reproducibility Constraint

| Rule ID | Rule |
|---|---|
| `REP-001` | Every match must be replay-loggable from Phase 2 onward. |
| `REP-002` | Replay files must include config, seed, version, frames, and events. |
| `REP-003` | Replay frame order is strictly increasing by `tick`. |
| `REP-004` | Replay playback must not recompute combat logic. It renders saved frames/events. |
| `REP-005` | Replay schema version must be explicit. |

### 2.3 Rendering Decoupling Constraint

| Rule ID | Rule |
|---|---|
| `REN-001` | Renderer may read `ReplayFrame`, `MatchStateSnapshot`, and `EventLog`. |
| `REN-002` | Renderer may not import simulator internals except public snapshot schemas. |
| `REN-003` | Renderer may not resolve attacks, movement, cooldowns, deaths, or rewards. |
| `REN-004` | Renderer must support offline replay playback. |
| `REN-005` | Training must run without renderer dependencies installed. |

### 2.4 Headless Training Constraint

| Rule ID | Rule |
|---|---|
| `TRL-001` | RL environments must run with `render_mode=None` by default. |
| `TRL-002` | Training loops must not require Pygame, browser, FastAPI, or frontend code. |
| `TRL-003` | Training performance must be benchmarked in headless mode only. |
| `TRL-004` | Replay capture during training must be optional and rate-limited. |

### 2.5 Vertical-Slice Development Constraint

Each phase must produce:

1. runnable code,
2. tests,
3. at least one saved artifact,
4. validation output,
5. documented completion criteria.

### 2.6 Modular Architecture Constraint

Modules may depend only on lower-level stable interfaces.

```text
frontend -> backend API -> replay/evaluation artifacts
renderer -> replay schemas
training -> env wrappers -> simulator public API
agents -> simulator public API + profiles
simulator -> core schemas + config
```

Forbidden dependencies:

```text
simulator -> renderer
simulator -> frontend
simulator -> training
simulator -> LLM/NLP
renderer -> training internals
frontend -> simulator internals
NLP parser -> simulator internals
```

### 2.7 Interface-First Design Constraint

Public interfaces include:

- `SimulationConfig`
- `EnvironmentConfig`
- `MatchState`
- `AgentState`
- `ActionDefinition`
- `ObservationVector`
- `RewardBreakdown`
- `ReplayFrame`
- `EventLog`
- `BehaviorProfile`
- `EvaluationResult`

Any change to these structures requires:

1. schema version bump if serialized,
2. test updates,
3. replay compatibility review,
4. documentation update in this spec.

### 2.8 Logging Requirements

| Layer | Required Logging |
|---|---|
| Simulator | seed, config hash, tick count, terminal condition, invariant failures |
| Agents | chosen action, invalid action fallback, target selection, behavior profile ID |
| RL wrapper | episode reward, termination/truncation cause, invalid action counts |
| Training | hyperparameters, checkpoint paths, evaluation scores |
| Replay | replay file path, schema version, frame count, event count |
| NLP | input command, validated profile, validation errors, fallback behavior |

### 2.9 Testing Requirements

Minimum required test categories:

1. schema validation tests,
2. deterministic simulation tests,
3. action validation tests,
4. reward calculation tests,
5. replay serialization tests,
6. renderer smoke tests,
7. Gymnasium API compliance tests,
8. RL sanity checks,
9. behavior profile differential tests.

### 2.10 Naming Conventions

| Object Type | Convention | Example |
|---|---|---|
| Python modules | snake_case | `combat_resolution.py` |
| Python classes | PascalCase | `MatchState` |
| Functions | snake_case | `resolve_combat()` |
| Constants | UPPER_SNAKE_CASE | `MAX_TEAM_SIZE` |
| Agent IDs | `team{n}_{role}_{index}` | `team0_tank_0` |
| Event types | snake_case string | `agent_damaged` |
| Config files | kebab-case YAML | `mvp-2v2-elimination.yaml` |
| Replay files | timestamp + scenario + seed | `2026-05-23_mvp-2v2_seed-42.jsonl` |

### 2.11 Serialization Requirements

| Artifact | Format | Reason |
|---|---|---|
| Configs | YAML | Human editable; stable diffs |
| Replay frames | JSONL | Streaming-friendly; debuggable |
| Replay metadata | JSON | Fast load; frontend-friendly |
| Metrics | JSON + CSV exports | Programmatic + spreadsheet analysis |
| Checkpoints | SB3 `.zip` and metadata JSON | Compatible with SB3 model saving |
| Behavior profiles | JSON/YAML | Human-readable and parser-friendly |

### 2.12 Versioning Rules

| Versioned Artifact | Version Field |
|---|---|
| Replay schema | `replay_schema_version` |
| Config schema | `config_schema_version` |
| Behavior profile schema | `profile_schema_version` |
| Observation schema | `observation_schema_version` |
| Action schema | `action_schema_version` |
| Evaluation metrics schema | `metrics_schema_version` |

---

## 3. Canonical Tech Stack

### 3.1 Required Runtime Stack

| Component | Exact Baseline | Required | Introduced | Purpose | Replacement Policy |
|---|---:|---:|---|---|---|
| Python | `3.12.x` | Yes | Phase 1 | Core simulator, agents, RL, evaluation | Do not downgrade below 3.10; prefer 3.12 for stability. |
| NumPy | `>=2.2,<3.0` | Yes | Phase 1 | Vector math, observations, metrics | Replace only with direct need for JAX/Torch tensors in simulator. |
| Pydantic | `>=2.7,<3.0` | Yes | Phase 1 | Schema validation for config/profile/NLP | Required for stable structured validation. |
| PyYAML | `>=6.0,<7.0` | Yes | Phase 1 | Config files | Replace with `ruamel.yaml` only if comments preservation is required. |
| orjson | `>=3.10,<4.0` | Optional | Phase 2 | Faster replay JSON serialization | Standard `json` allowed for MVP. |

### 3.2 RL / ML Stack

| Component | Exact Baseline | Required | Introduced | Purpose | Replacement Policy |
|---|---:|---:|---|---|---|
| Gymnasium | `1.3.0` | Yes | Phase 4 | Single-agent environment API | Must remain primary API for MVP training. |
| Stable-Baselines3 | `2.8.0` | Yes | Phase 5 | PPO training baseline | Replace only after MVP with custom PyTorch/RLlib. |
| PyTorch | `>=2.7,<3.0` | Yes via SB3 | Phase 5 | Neural network backend | Do not use directly in simulator core. |
| PettingZoo | `1.26.1` | Optional Post-MVP | Phase 13+ | Formal multi-agent API | Introduce after Gymnasium wrapper is stable. |
| Ray RLlib | Deferred | No | Advanced | Scalable MARL/distributed training | Do not introduce before research-grade stage. |
| MLflow or W&B | Optional | No | Phase 9+ | Experiment tracking | Start with local JSON/CSV; add one tracker later. |

### 3.3 Rendering and Visualization Stack

| Component | Baseline | Required | Introduced | Purpose | Replacement Policy |
|---|---|---:|---|---|---|
| Pygame CE or Pygame | Latest compatible with Python 3.12 | Yes for local debug renderer | Phase 2 | Simple replay/debug visualization | May be replaced by browser canvas after post-MVP dashboard. |
| Matplotlib | `>=3.9,<4.0` | Yes | Phase 9 | Offline plots, heatmaps, metrics | Keep for evaluation notebooks and reports. |
| Plotly | Optional | No | Phase 10+ | Interactive dashboard charts | Use only in frontend/backend dashboard stage. |

### 3.4 Backend Stack

| Component | Baseline | Required | Introduced | Purpose | Replacement Policy |
|---|---|---:|---|---|---|
| FastAPI | `>=0.115,<1.0` | Post-MVP | Phase 10 | Serve replay files, metrics, command parsing API | Not required for MVP. |
| Uvicorn | `>=0.30,<1.0` | Post-MVP | Phase 10 | Local API server | Standard FastAPI server. |
| SQLite | Python stdlib | Optional | Phase 9+ | Local experiment index | Use before Postgres. |
| PostgreSQL | `16+` | Optional | Phase 10+ | Persistent experiment storage | Introduce only after local artifacts become insufficient. |
| Redis | Deferred | No | Advanced | Caching/queues | Do not introduce before backend has real async needs. |

### 3.5 Frontend Stack

| Component | Baseline | Required | Introduced | Purpose | Replacement Policy |
|---|---|---:|---|---|---|
| Node.js | `22 LTS` | Post-MVP | Phase 10 | Frontend runtime | Use active LTS only. |
| TypeScript | `>=5.5` | Post-MVP | Phase 10 | Typed frontend | Required if frontend exists. |
| React | `>=19` | Post-MVP | Phase 10 | UI components | Use with Vite or Next.js. |
| Vite | `>=6` | Recommended | Phase 10 | Lightweight frontend build | Prefer Vite over Next.js unless server rendering is needed. |
| Tailwind CSS | `>=4` | Optional | Phase 10 | UI styling | Can be replaced with plain CSS for faster MVP. |
| PixiJS or Canvas API | Optional | Phase 10 | Browser replay rendering | Start with plain Canvas unless complex scenes require PixiJS. |

### 3.6 Testing and Quality Stack

| Tool | Baseline | Required | Introduced | Purpose |
|---|---:|---:|---|---|
| pytest | `>=8.0,<9.0` | Yes | Phase 1 | Unit/integration tests |
| hypothesis | `>=6.0,<7.0` | Optional | Phase 3+ | Property tests for invariants |
| ruff | `>=0.8,<1.0` | Yes | Phase 1 | Lint and formatting |
| mypy | `>=1.10,<2.0` | Recommended | Phase 1 | Static typing |
| pre-commit | `>=4.0,<5.0` | Recommended | Phase 1 | Local checks |

### 3.7 Packaging and Dependency Management

| Tool | Baseline | Required | Introduced | Purpose |
|---|---:|---:|---|---|
| uv | `>=0.5` | Recommended | Phase 0 | Fast Python dependency management |
| pyproject.toml | PEP 621 | Yes | Phase 0 | Project metadata and dependencies |
| Docker | Current stable | Optional | Phase 10+ | Reproducible backend/frontend deployments |
| Docker Compose | Current stable | Optional | Phase 10+ | Local service orchestration |

### 3.8 Hardware Recommendations

| Tier | Hardware | Expected Use |
|---|---|---|
| Minimum | Modern laptop CPU, 16 GB RAM | Simulator, heuristics, replay, small PPO runs |
| Recommended | 8+ CPU cores, 32 GB RAM, NVIDIA GPU optional | Vectorized PPO experiments, faster evaluation |
| Advanced | Dedicated GPU + 64 GB RAM | Larger policies, self-play, MARL experiments |

MVP must remain usable on CPU. GPU acceleration is optional and must not be assumed by tests.

---

## 4. Repository Architecture

### 4.1 Canonical Repository Tree

```text
combatrl/
  README.md
  pyproject.toml
  uv.lock
  .gitignore
  .pre-commit-config.yaml
  configs/
    env/
      mvp_1v1.yaml
      mvp_2v2_elimination.yaml
      mvp_2v2_objective.yaml
    training/
      ppo_1v1_baseline.yaml
      ppo_2v2_baseline.yaml
    profiles/
      aggressive.yaml
      defensive.yaml
      kiter.yaml
      protective.yaml
  src/
    combatrl/
      __init__.py
      core/
        __init__.py
        constants.py
        ids.py
        rng.py
        geometry.py
        types.py
      schemas/
        __init__.py
        agent_state.py
        match_state.py
        actions.py
        observations.py
        rewards.py
        replay.py
        profiles.py
        configs.py
        evaluation.py
      sim/
        __init__.py
        engine.py
        movement.py
        targeting.py
        combat.py
        cooldowns.py
        obstacles.py
        win_conditions.py
        invariants.py
        snapshots.py
      agents/
        __init__.py
        base.py
        random_bot.py
        aggressive_bot.py
        defensive_bot.py
        kiter_bot.py
        protector_bot.py
        utility.py
      profiles/
        __init__.py
        loader.py
        validators.py
        modulation.py
      replay/
        __init__.py
        writer.py
        reader.py
        schemas.py
        validators.py
      renderer/
        __init__.py
        pygame_renderer.py
        overlays.py
        camera.py
      envs/
        __init__.py
        gym_env.py
        wrappers.py
        action_codec.py
        observation_builder.py
        reward_builder.py
      training/
        __init__.py
        train_ppo.py
        evaluate_checkpoint.py
        callbacks.py
        registry.py
      evaluation/
        __init__.py
        metrics.py
        benchmark_suite.py
        aggregate.py
        reports.py
      nlp/
        __init__.py
        parser.py
        prompts.py
        fallback_rules.py
        validation.py
      backend/
        __init__.py
        app.py
        routes_replays.py
        routes_metrics.py
        routes_commands.py
      scripts/
        __init__.py
  frontend/
    package.json
    tsconfig.json
    vite.config.ts
    src/
      main.tsx
      api/
        client.ts
        types.ts
      components/
        ReplayViewer.tsx
        MetricsPanel.tsx
        CommandInput.tsx
        ProfileInspector.tsx
        ComparisonView.tsx
      render/
        canvasRenderer.ts
        coordinateTransforms.ts
      pages/
        App.tsx
  tests/
    unit/
      test_geometry.py
      test_actions.py
      test_rewards.py
      test_profiles.py
    integration/
      test_sim_determinism.py
      test_replay_roundtrip.py
      test_gym_env_contract.py
      test_heuristic_matches.py
    rl/
      test_random_policy_rollout.py
      test_short_ppo_smoke.py
  notebooks/
    evaluation_analysis.ipynb
  artifacts/
    replays/
      .gitkeep
    metrics/
      .gitkeep
    checkpoints/
      .gitkeep
    reports/
      .gitkeep
  scripts/
    run_match.py
    render_replay.py
    train_ppo.py
    evaluate_policy.py
    compare_profiles.py
    validate_replay.py
  docs/
    CombatRL_Canonical_Project_Spec.md
    architecture.md
    replay_schema.md
    rl_training.md
```

### 4.2 Directory Responsibilities

| Directory | Responsibility | Public Interfaces | Internal-Only Components |
|---|---|---|---|
| `core/` | Low-level utilities and type aliases | `rng`, `geometry`, `ids` | None |
| `schemas/` | Public data contracts | All schema classes | None; all schemas are public contracts |
| `sim/` | Deterministic simulation logic | `SimulationEngine`, snapshots | Movement/combat helper internals |
| `agents/` | Heuristic and utility agents | `AgentPolicy`, baseline bot classes | Bot-specific heuristics |
| `profiles/` | Behavior profile loading/modulation | `BehaviorProfile`, `apply_profile_modulation` | Profile weighting internals |
| `replay/` | Replay read/write/validation | `ReplayWriter`, `ReplayReader` | Storage implementation details |
| `renderer/` | Local debug rendering | `render_replay()` | Pygame event loop details |
| `envs/` | Gymnasium wrappers | `CombatRLGymEnv` | Observation/action encoders |
| `training/` | PPO and evaluation scripts | CLI entrypoints | SB3 callback details |
| `evaluation/` | Metrics and benchmark suites | `EvaluationResult`, `BenchmarkSuite` | Aggregation internals |
| `nlp/` | Language-to-profile conversion | `parse_command_to_profile()` | Prompt templates, fallback rules |
| `backend/` | Optional API server | FastAPI app | Route internals |
| `frontend/` | Optional browser dashboard | API type contracts | UI implementation details |

### 4.3 Import Boundaries

Allowed imports:

```text
schemas -> core
sim -> core, schemas
agents -> core, schemas, sim public API, profiles
profiles -> schemas
replay -> schemas, core
renderer -> schemas, replay
envs -> schemas, sim, agents, profiles
evaluation -> schemas, replay, envs optional
training -> envs, evaluation, profiles
nlp -> schemas.profiles, profiles.validators
backend -> replay, evaluation, nlp
frontend -> backend API only
```

Forbidden imports:

```text
sim -> renderer
sim -> envs
sim -> training
sim -> backend
sim -> frontend
schemas -> sim
schemas -> agents
renderer -> sim internals
nlp -> agents or sim internals
frontend -> Python simulator internals
```

### 4.4 File Naming Standards

1. One primary public class per schema file.
2. Test files mirror source module names.
3. CLI scripts use verbs: `run_match.py`, `render_replay.py`, `evaluate_policy.py`.
4. Config names encode mode and purpose: `mvp_2v2_elimination.yaml`.
5. No file may contain both simulator logic and rendering logic.

---

## 5. Global Data Models

### 5.1 Shared Type Conventions

| Type Name | Concrete Type | Meaning |
|---|---|---|
| `AgentID` | `str` | Stable unique ID for an agent in a match |
| `TeamID` | `int` | `0` or `1` in MVP |
| `Tick` | `int` | Integer simulation step index |
| `Seconds` | `float` | Real-time equivalent used for display only |
| `Position2D` | tuple/list of two floats | `(x, y)` in arena coordinates |
| `Velocity2D` | tuple/list of two floats | `(vx, vy)` per second |
| `NormalizedFloat` | `float` | Must be in `[0.0, 1.0]` |

### 5.2 `AgentState`

Ownership: `schemas/agent_state.py`  
Serialized: yes, in replay frames  
Mutable source of truth: simulation engine  

```python
class AgentState(BaseModel):
    agent_id: str
    team_id: int
    role: Literal["tank", "ranged_dps", "support"]
    position: tuple[float, float]
    velocity: tuple[float, float]
    hp: float
    max_hp: float
    alive: bool
    attack_cooldown_ticks: int
    ability_cooldown_ticks: int
    status_effects: list[str]
    current_target_id: str | None
    last_action_id: int | None
```

| Field | Type | Semantics | Invariants |
|---|---|---|---|
| `agent_id` | string | Stable identifier | Unique within match |
| `team_id` | int | Team membership | MVP: `0` or `1` |
| `role` | enum | Role archetype | MVP supports `tank`, `ranged_dps`; `support` reserved |
| `position` | `(float, float)` | Arena coordinates | Must remain inside arena after resolution |
| `velocity` | `(float, float)` | Current velocity | Derived from action; may be zero |
| `hp` | float | Current health | `0 <= hp <= max_hp` |
| `max_hp` | float | Maximum health | `> 0` |
| `alive` | bool | Combat participation | `alive == (hp > 0)` after death resolution |
| `attack_cooldown_ticks` | int | Basic attack cooldown | `>= 0` |
| `ability_cooldown_ticks` | int | Class ability cooldown | `>= 0` |
| `status_effects` | list | Active effects | Empty in MVP unless effects implemented |
| `current_target_id` | nullable string | Current intended target | Must reference existing live entity or be null |
| `last_action_id` | nullable int | Last decoded action | Must exist in action schema if not null |

### 5.3 `MatchState`

Ownership: `schemas/match_state.py`  
Serialized: snapshots only; full mutable object stays in simulator  

```python
class MatchState(BaseModel):
    match_id: str
    seed: int
    tick: int
    max_ticks: int
    tick_rate_hz: int
    arena_width: float
    arena_height: float
    agents: dict[str, AgentState]
    obstacles: list[ObstacleState]
    terminal: bool
    winner_team_id: int | None
    terminal_reason: str | None
```

Invariants:

1. `tick >= 0`.
2. `tick <= max_ticks`.
3. `agents` keys equal each `AgentState.agent_id`.
4. No two live agents occupy invalid positions after movement resolution.
5. `terminal == True` implies `terminal_reason is not None`.
6. `winner_team_id` is null for draw/timeouts unless score rules decide winner.

### 5.4 `ReplayFrame`

Ownership: `schemas/replay.py` and `replay/schemas.py`  
Serialization: JSONL, one frame per logged tick  

```python
class ReplayFrame(BaseModel):
    replay_schema_version: str
    match_id: str
    tick: int
    sim_time_seconds: float
    agents: list[AgentState]
    events: list[EventLog]
    scoreboard: dict[str, float | int | str | None]
```

Frame invariants:

1. `tick` strictly increases by logging interval.
2. `sim_time_seconds == tick / tick_rate_hz`.
3. `events` contain only events that occurred at this tick.
4. Agent list order sorted by `agent_id`.

### 5.5 `EventLog`

```python
class EventLog(BaseModel):
    event_id: str
    tick: int
    event_type: str
    source_agent_id: str | None
    target_agent_id: str | None
    payload: dict[str, Any]
```

Canonical event types:

| Event Type | Required Payload |
|---|---|
| `match_started` | `config_hash`, `seed` |
| `agent_action_selected` | `action_id`, `action_name`, `valid`, `fallback_used` |
| `agent_moved` | `from`, `to` |
| `agent_attacked` | `target_id`, `damage`, `in_range` |
| `agent_damaged` | `amount`, `hp_before`, `hp_after` |
| `agent_eliminated` | `eliminated_by` |
| `ability_used` | `ability_name`, `target_id` |
| `cooldown_started` | `cooldown_name`, `duration_ticks` |
| `match_ended` | `winner_team_id`, `reason` |

### 5.6 `ObservationVector`

Ownership: `schemas/observations.py` and `envs/observation_builder.py`  
Serialization: not stored by default; optional debug artifact  

```python
class ObservationVector(BaseModel):
    observation_schema_version: str
    agent_id: str
    values: list[float]
    feature_names: list[str]
```

Invariants:

1. `len(values) == len(feature_names)`.
2. All values must be finite floats.
3. Normalized features should be in `[-1.0, 1.0]` or `[0.0, 1.0]` as specified in Section 8.
4. Feature ordering must remain stable within a schema version.

### 5.7 `ActionDefinition`

Ownership: `schemas/actions.py` and `envs/action_codec.py`

```python
class ActionDefinition(BaseModel):
    action_schema_version: str
    action_id: int
    action_name: str
    movement_intent: str
    combat_intent: str
    target_intent: str
    allowed_roles: list[str]
```

### 5.8 `RewardBreakdown`

```python
class RewardBreakdown(BaseModel):
    agent_id: str
    tick: int
    total_reward: float
    components: dict[str, float]
```

Required component keys in MVP:

```text
win_bonus
loss_penalty
damage_dealt
damage_taken_penalty
death_penalty
ally_death_penalty
invalid_action_penalty
time_penalty
```

### 5.9 `BehaviorProfile`

```python
class BehaviorProfile(BaseModel):
    profile_schema_version: str = "1.0"
    profile_id: str
    aggression: float
    caution: float
    cohesion: float
    protectiveness: float
    focus_fire: float
    greed: float
    spacing: float
    objective_bias: float
    notes: str | None = None
```

All behavior axes must satisfy `0.0 <= value <= 1.0`.

### 5.10 `EvaluationResult`

```python
class EvaluationResult(BaseModel):
    metrics_schema_version: str
    evaluation_id: str
    scenario_id: str
    policy_id: str
    opponent_id: str
    profile_id: str | None
    num_matches: int
    seed_start: int
    aggregate_metrics: dict[str, float]
    per_match_metrics_path: str
    replay_sample_paths: list[str]
```

### 5.11 `SimulationConfig`

```python
class SimulationConfig(BaseModel):
    config_schema_version: str
    scenario_id: str
    tick_rate_hz: int
    max_ticks: int
    arena_width: float
    arena_height: float
    teams: list[TeamConfig]
    obstacles: list[ObstacleConfig]
    win_condition: Literal["elimination", "objective_control"]
```

MVP defaults:

```yaml
config_schema_version: "1.0"
scenario_id: "mvp_2v2_elimination"
tick_rate_hz: 20
max_ticks: 1200
arena_width: 100.0
arena_height: 60.0
win_condition: elimination
```

### 5.12 `EnvironmentConfig`

```python
class EnvironmentConfig(BaseModel):
    env_id: str
    controlled_agent_id: str
    opponent_policy_ids: list[str]
    reward_config: dict[str, float]
    observation_schema_version: str
    action_schema_version: str
    capture_replays: bool
    replay_sample_rate: float
```

---

## 6. Core Simulation Architecture

### 6.1 Simulator Responsibilities

The simulation engine owns:

1. authoritative match state,
2. tick progression,
3. movement resolution,
4. targeting validation,
5. combat resolution,
6. cooldown progression,
7. death handling,
8. win-condition checking,
9. event generation,
10. invariant validation.

The simulator does **not** own:

- rendering,
- RL training,
- frontend APIs,
- natural-language parsing,
- metrics aggregation beyond raw event/frame generation.

### 6.2 Simulation Timing

MVP timing constants:

| Parameter | Value |
|---|---:|
| Simulation tick rate | `20 Hz` |
| Tick duration | `0.05 seconds` |
| Policy decision rate | `5 Hz` |
| Decision interval | `4 simulation ticks` |
| Default max match length | `1200 ticks` = `60 seconds` |

The simulator updates every tick. Agent policies may repeat the previous action for `decision_interval_ticks` unless a new action is requested.

### 6.3 Deterministic Tick Order

Every simulation tick must execute in this exact order:

1. Increment or confirm current tick index.
2. Request/receive actions for agents whose decision interval is due.
3. Validate actions and apply fallback actions if invalid.
4. Resolve movement intents into desired velocity.
5. Apply movement simultaneously using stable agent ordering.
6. Resolve wall and obstacle collisions.
7. Decrement cooldowns.
8. Resolve combat intents.
9. Apply damage/healing/status effects.
10. Resolve deaths.
11. Update target references.
12. Check win conditions.
13. Emit events.
14. Create replay frame if logging interval matches.
15. Run invariants in debug/test mode.

### 6.4 Stable Agent Ordering

Whenever multiple agents are processed, order by:

```text
(team_id ASC, role_priority ASC, agent_id ASC)
```

Role priority:

```text
tank = 0
ranged_dps = 1
support = 2
```

This avoids nondeterministic ordering from dictionary iteration.

### 6.5 Main Loop Pseudocode

```python
def run_match(config: SimulationConfig, policies: dict[AgentID, AgentPolicy], seed: int) -> MatchResult:
    rng = ProjectRNG(seed)
    state = initialize_match_state(config, rng)
    replay_writer.on_match_started(state, config)

    while not state.terminal and state.tick < state.max_ticks:
        due_agents = get_agents_due_for_decision(state)
        proposed_actions = {}

        for agent_id in sorted_due_agent_ids(due_agents, state):
            obs = build_agent_observation(state, agent_id)
            action = policies[agent_id].select_action(obs, state.public_snapshot(agent_id))
            proposed_actions[agent_id] = action

        validated_actions = validate_or_fallback_actions(state, proposed_actions)
        movement_commands = resolve_movement_intents(state, validated_actions)
        apply_simultaneous_movement(state, movement_commands)
        resolve_collisions(state)
        decrement_cooldowns(state)
        combat_events = resolve_combat_intents(state, validated_actions)
        apply_combat_events(state, combat_events)
        resolve_deaths(state)
        refresh_targets(state)
        check_win_conditions(state)
        validate_invariants_if_enabled(state)
        replay_writer.capture_frame(state, events_for_tick)
        state.tick += 1

    replay_writer.on_match_ended(state)
    return build_match_result(state)
```

### 6.6 Movement Resolution

Movement intents map to a desired direction vector. The simulator then applies role speed and tick duration.

```text
new_position = old_position + normalize(direction) * role_speed * tick_duration
```

Movement rules:

1. Dead agents do not move.
2. Zero vector movement results in hold position.
3. Movement is clamped to arena bounds.
4. Obstacle collision uses simple circle-vs-rectangle pushback in MVP.
5. Agent-agent collision may be ignored in MVP or handled as soft separation; it must be deterministic if implemented.

### 6.7 Combat Resolution

MVP combat rules:

1. Basic attacks are instant if target is valid, alive, enemy, and in range.
2. Attacks require `attack_cooldown_ticks == 0`.
3. Attack damage is role-defined.
4. Attack starts cooldown immediately after successful attack.
5. Out-of-range attack produces an `agent_attacked` event with `in_range=false` and no damage.
6. Invalid target attack falls back to nearest valid target only if action definition allows target fallback.

### 6.8 Role Defaults

| Role | HP | Speed | Attack Range | Damage | Attack Cooldown |
|---|---:|---:|---:|---:|---:|
| `tank` | `160` | `7.0` | `5.0` | `12` | `12 ticks` |
| `ranged_dps` | `90` | `8.5` | `18.0` | `10` | `8 ticks` |
| `support` | `80` | `8.0` | `14.0` | `5` | `10 ticks` |

`support` is reserved until Future Expansion Contracts unless specifically implemented in post-MVP.

### 6.9 Death Handling

Death rules:

1. If `hp <= 0`, set `hp = 0`, `alive = false`.
2. Emit `agent_eliminated` once per agent.
3. Clear target references pointing to dead agents in the refresh target phase.
4. Dead agents remain in observations with `alive = 0` and zeroed relative features.

### 6.10 Win Conditions

MVP win condition: `elimination`.

```python
team_alive_counts = count_live_agents_by_team(state)
if exactly_one_team_has_live_agents(team_alive_counts):
    terminal = True
    winner_team_id = that_team
elif state.tick >= state.max_ticks:
    terminal = True
    winner_team_id = team_with_more_total_hp_or_none
```

Tie-break order at timeout:

1. More live agents.
2. Higher total remaining HP.
3. More total damage dealt.
4. Draw if still tied.

### 6.11 Simulation Invariants

Required invariant checks:

1. No NaN or infinite positions.
2. HP always in `[0, max_hp]`.
3. Cooldowns always `>= 0`.
4. Alive status matches HP after death handling.
5. Agent positions within arena bounds.
6. Target IDs reference existing agents or null.
7. Terminal state contains terminal reason.
8. Replay frame tick equals simulation tick when captured.

---

## 7. Action System Specification

### 7.1 Action Architecture

The MVP uses discrete tactical actions composed of three dimensions:

1. `movement_intent`
2. `combat_intent`
3. `target_intent`

The environment exposes a flattened discrete action ID to RL algorithms. Internally, the action ID decodes into the structured action definition.

### 7.2 Movement Intents

| Movement Intent | Semantics |
|---|---|
| `hold_position` | No movement. |
| `move_toward_target` | Move toward selected target if available; otherwise hold. |
| `move_away_from_target` | Move directly away from selected target if available; otherwise hold. |
| `move_toward_ally` | Move toward nearest or selected ally. |
| `move_away_from_danger` | Move away from nearest enemy or high-threat enemy. |
| `strafe_left` | Move perpendicular left relative to target direction. |
| `strafe_right` | Move perpendicular right relative to target direction. |
| `move_to_center` | Move toward arena center or objective center. |

### 7.3 Combat Intents

| Combat Intent | Semantics | Cooldown Required |
|---|---|---:|
| `no_op` | No combat action. | No |
| `basic_attack` | Attack selected enemy target. | Yes |
| `class_ability` | Use role-specific ability. | Yes |
| `defensive_ability` | Reserved for future. | Yes |
| `support_ally` | Reserved for support/healing. | Yes |

### 7.4 Target Intents

| Target Intent | Semantics |
|---|---|
| `nearest_enemy` | Live enemy with minimum distance. |
| `lowest_hp_enemy` | Live enemy with lowest normalized HP. |
| `enemy_dps` | Live enemy role `ranged_dps`; nearest if multiple. |
| `enemy_tank` | Live enemy role `tank`; nearest if multiple. |
| `ally_lowest_hp` | Live ally with lowest normalized HP. |
| `ally_under_threat` | Ally closest to an enemy or recently damaged. |
| `current_target` | Keep previous target if valid. |

### 7.5 Discrete Action Mapping

MVP action space is generated as the Cartesian product of:

```text
movement_intents = 8
combat_intents = 3  # no_op, basic_attack, class_ability
target_intents = 7
```

Maximum base action count:

```text
8 * 3 * 7 = 168 actions
```

Actions invalid for a role are masked or converted to fallback.

### 7.6 Action Encoding Contract

Ownership: `envs/action_codec.py`

Required methods:

```python
class ActionCodec:
    def __init__(self, action_definitions: list[ActionDefinition]): ...
    def n_actions(self) -> int: ...
    def decode(self, action_id: int) -> ActionDefinition: ...
    def encode(self, movement_intent: str, combat_intent: str, target_intent: str) -> int: ...
    def valid_action_mask(self, state: MatchState, agent_id: str) -> np.ndarray: ...
    def fallback_action(self, state: MatchState, agent_id: str) -> int: ...
```

### 7.7 Invalid Action Behavior

Invalid action handling must be deterministic.

| Invalid Condition | MVP Behavior |
|---|---|
| Action ID outside range | Replace with fallback `hold/no_op/current_target`; apply invalid penalty. |
| Combat target unavailable | Movement may execute; combat intent becomes `no_op`. |
| Ability on cooldown | Ability intent becomes `no_op`; cooldown violation event emitted. |
| Role cannot use action | Replace with fallback; apply invalid penalty. |
| Agent dead | Action ignored; no penalty emitted for dead agents. |

### 7.8 Action Masking

Action masks must indicate valid actions before RL policy selection where supported.

MVP SB3 PPO does not natively use action masks in baseline PPO. Therefore:

1. The environment must validate actions regardless of masks.
2. Optional `sb3-contrib MaskablePPO` can be added later.
3. Heuristic agents and behavior-profile reranking must respect masks immediately.

### 7.9 Role-Specific Action Rules

| Role | Allowed MVP Combat Intents |
|---|---|
| `tank` | `no_op`, `basic_attack`, `class_ability` where class ability is short engage/guard placeholder |
| `ranged_dps` | `no_op`, `basic_attack`, `class_ability` where class ability is high-damage shot placeholder |
| `support` | Deferred; future: `support_ally`, `basic_attack`, `class_ability` |

---

## 8. Observation System Specification

### 8.1 Observation Architecture

Observations are structured numeric vectors. Raw pixels are forbidden for MVP.

The observation builder consumes `MatchState` and `agent_id`, then emits a fixed-length vector with stable feature ordering.

Ownership: `envs/observation_builder.py`

### 8.2 Normalization Rules

| Feature Type | Normalization |
|---|---|
| Position x | `x / arena_width` scaled to `[0,1]` |
| Position y | `y / arena_height` scaled to `[0,1]` |
| Relative dx | `dx / arena_width` clipped to `[-1,1]` |
| Relative dy | `dy / arena_height` clipped to `[-1,1]` |
| Distance | `distance / max(arena_width, arena_height)` clipped to `[0,1]` |
| HP | `hp / max_hp` |
| Cooldown | `cooldown_ticks / max_cooldown_ticks` clipped to `[0,1]` |
| Alive | `1.0` if alive else `0.0` |
| Role | one-hot vector |

### 8.3 MVP Observation Ordering

Observation vector layout for controlled agent:

| Segment | Count | Description |
|---|---:|---|
| Self features | 10 | HP, position, cooldowns, velocity, role one-hot |
| Ally slot 1 | 9 | Alive, relative pos, distance, HP, role one-hot, threat indicator |
| Enemy slot 1 | 9 | Alive, relative pos, distance, HP, role one-hot, in_attack_range |
| Enemy slot 2 | 9 | Same as enemy slot 1 |
| Arena features | 6 | Wall distances, center relative pos |
| Tactical features | 6 | nearest enemy distance, ally distance, outnumbered flag, recent damage flags |
| Total MVP | 49 | Fixed length |

### 8.4 Self Feature Layout

| Index | Name | Range |
|---:|---|---|
| 0 | `self_hp_norm` | `[0,1]` |
| 1 | `self_x_norm` | `[0,1]` |
| 2 | `self_y_norm` | `[0,1]` |
| 3 | `self_vx_norm` | `[-1,1]` |
| 4 | `self_vy_norm` | `[-1,1]` |
| 5 | `self_attack_cd_norm` | `[0,1]` |
| 6 | `self_ability_cd_norm` | `[0,1]` |
| 7 | `role_tank` | `{0,1}` |
| 8 | `role_ranged_dps` | `{0,1}` |
| 9 | `role_support` | `{0,1}` |

### 8.5 Entity Slot Ordering

All non-self entities must be sorted deterministically.

Allies:

1. Live allies before dead allies.
2. Increasing distance to self.
3. `agent_id` alphabetical tie-break.

Enemies:

1. Live enemies before dead enemies.
2. Increasing distance to self.
3. `agent_id` alphabetical tie-break.

### 8.6 Missing Entity Handling

If a slot does not exist:

1. `alive = 0.0`
2. relative position = `0.0, 0.0`
3. distance = `1.0`
4. HP = `0.0`
5. role one-hot = all zeros
6. tactical flags = `0.0`

### 8.7 Visibility Rules

MVP uses full observability. Fog of war is forbidden until Future Expansion Contracts.

### 8.8 Observation Validation

Required checks:

1. fixed vector length,
2. no NaN,
3. no infinite values,
4. all normalized values within documented ranges,
5. stable feature names across repeated calls.

---

## 9. Reward System Specification

### 9.1 Reward Architecture

Reward generation is separated from simulation state mutation.

Ownership:

- `envs/reward_builder.py` for Gymnasium reward emission.
- `schemas/rewards.py` for `RewardBreakdown`.
- `evaluation/metrics.py` for post-hoc metrics.

### 9.2 MVP Reward Components

| Component | Formula | Trigger | Default Scale |
|---|---|---|---:|
| `win_bonus` | `+1.0` | Controlled team wins | `1.0` |
| `loss_penalty` | `-1.0` | Controlled team loses | `1.0` |
| `damage_dealt` | `damage / 100.0` | Controlled agent damages enemy | `1.0` |
| `damage_taken_penalty` | `-damage / 150.0` | Controlled agent takes damage | `1.0` |
| `death_penalty` | `-0.5` | Controlled agent dies | `1.0` |
| `ally_death_penalty` | `-0.25` | Controlled ally dies | `1.0` |
| `invalid_action_penalty` | `-0.02` | Invalid controlled action | `1.0` |
| `time_penalty` | `-0.001` | Every decision step | `1.0` |

### 9.3 Team Reward

For 2v2 training, final reward may include team outcome:

```text
total_reward = individual_dense_reward + team_outcome_reward
```

Do not give dense team damage rewards until individual behavior is stable.

### 9.4 Role Reward Additions

Role-specific rewards are optional and must be small.

| Role | Optional Reward | Formula | Risk |
|---|---|---|---|
| `tank` | Ally protection | small positive if closer to enemy than ally DPS | Tank may body-block uselessly |
| `ranged_dps` | Spacing | positive for staying in attack range while outside enemy tank range | May kite forever |
| `support` | Effective healing | healing that prevents ally death | Credit assignment complexity |

### 9.5 Anti-Exploit Safeguards

| Exploit | Symptom | Mitigation |
|---|---|---|
| Damage farming without winning | High damage, low win rate | Keep win/loss bonus meaningful. |
| Infinite kiting | Long matches, low engagement | Time penalty and objective mode later. |
| Suicide damage | High early damage, frequent death | Death penalty and damage-taken penalty. |
| Invalid action spam | Many invalid actions | Invalid penalty and action masks. |
| Teammate neglect | Ally dies early | Ally death penalty and teamwork metrics. |

### 9.6 Reward Validation Tests

Required tests:

1. damage dealt increases reward,
2. damage taken decreases reward,
3. win terminal reward is positive,
4. loss terminal reward is negative,
5. invalid action penalty is applied once per invalid action,
6. zero-event step produces only time penalty,
7. reward breakdown sums exactly to total reward.

---

## 10. Replay System Specification

### 10.1 Replay Architecture

Replay system components:

| Component | File | Responsibility |
|---|---|---|
| `ReplayWriter` | `replay/writer.py` | Stream metadata, frames, events to disk. |
| `ReplayReader` | `replay/reader.py` | Load metadata and iterate frames. |
| `ReplayValidator` | `replay/validators.py` | Verify schema and invariants. |
| `ReplayFrame` schema | `schemas/replay.py` | Public frame contract. |

### 10.2 Replay Storage Layout

```text
artifacts/replays/
  2026-05-23_mvp-2v2_seed-42/
    metadata.json
    frames.jsonl
    events.jsonl
    summary.json
```

### 10.3 `metadata.json` Schema

```json
{
  "replay_schema_version": "1.0",
  "match_id": "mvp_2v2_seed_42_001",
  "scenario_id": "mvp_2v2_elimination",
  "seed": 42,
  "config_hash": "sha256:...",
  "tick_rate_hz": 20,
  "decision_rate_hz": 5,
  "created_at_utc": "2026-05-23T00:00:00Z",
  "combatrl_version": "0.1.0"
}
```

### 10.4 `frames.jsonl` Schema

Each line is one `ReplayFrame` JSON object.

```json
{
  "replay_schema_version": "1.0",
  "match_id": "mvp_2v2_seed_42_001",
  "tick": 40,
  "sim_time_seconds": 2.0,
  "agents": [],
  "events": [],
  "scoreboard": {
    "team0_alive": 2,
    "team1_alive": 2,
    "team0_total_hp": 250.0,
    "team1_total_hp": 210.0
  }
}
```

### 10.5 Logging Frequency

MVP default:

| Replay Type | Logging Frequency |
|---|---:|
| Debug match | Every simulation tick |
| Training sample replay | Every 4 ticks |
| Large evaluation replay | Every 4 or 10 ticks |

Events must always be logged at exact tick regardless of frame sampling.

### 10.6 Deterministic Replay Guarantees

Replay playback uses saved frames only. Deterministic recomputation replay is optional and deferred.

Validation guarantee:

1. Metadata seed/config exists.
2. Frames load in ascending tick order.
3. All frame agent states pass schema validation.
4. Terminal summary agrees with final frame.

---

## 11. Rendering System Specification

### 11.1 Renderer Responsibilities

Renderer must:

1. load replay files,
2. draw arena bounds,
3. draw obstacles,
4. draw agents,
5. draw HP bars,
6. draw attack ranges optionally,
7. draw target lines optionally,
8. show playback controls,
9. show current tick/time,
10. show selected debug overlays.

### 11.2 Renderer Non-Responsibilities

Renderer must not:

1. compute attacks,
2. compute movement,
3. modify agent state,
4. decide targets,
5. compute rewards,
6. train policies,
7. alter replay files except optional annotation exports.

### 11.3 Local Debug Renderer

File: `renderer/pygame_renderer.py`

Required public function:

```python
def render_replay(replay_path: str, playback_speed: float = 1.0, overlays: list[str] | None = None) -> None:
    ...
```

### 11.4 Debug Overlays

| Overlay | Description | Phase |
|---|---|---|
| `hp_bars` | Current HP above agents | Phase 2 |
| `attack_ranges` | Circle around selected/all agents | Phase 2 |
| `target_lines` | Line from source to current target | Phase 2 |
| `velocity_vectors` | Movement direction arrows | Phase 3 |
| `event_feed` | Recent combat/action events | Phase 3 |
| `trajectory_trails` | Historical movement trail | Phase 9 |
| `profile_axes` | Current behavior profile values | Phase 10+ |

### 11.5 Coordinate System

Simulation coordinate origin is bottom-left or top-left, but must be globally consistent. MVP chooses:

```text
Simulation origin: bottom-left
Renderer origin: top-left screen coordinates
```

Renderer must convert:

```python
screen_x = sim_x * scale + offset_x
screen_y = screen_height - (sim_y * scale + offset_y)
```

---

## 12. Heuristic Agent System

### 12.1 Bot Interface

Ownership: `agents/base.py`

```python
class AgentPolicy(Protocol):
    policy_id: str

    def select_action(
        self,
        observation: ObservationVector,
        public_state: MatchState,
        agent_id: str,
        action_codec: ActionCodec,
        behavior_profile: BehaviorProfile | None = None,
    ) -> int:
        ...
```

### 12.2 Utility Function Interface

Ownership: `agents/utility.py`

```python
def score_action(
    action: ActionDefinition,
    state: MatchState,
    agent_id: str,
    profile: BehaviorProfile,
) -> float:
    ...
```

### 12.3 Baseline Bots

#### 12.3.1 Random Bot

File: `agents/random_bot.py`

Behavior:

1. Get valid action mask.
2. Uniformly sample valid action using project RNG.
3. Fallback to safe no-op if no valid action.

Purpose:

- API testing,
- baseline opponent,
- stochastic environment smoke tests.

#### 12.3.2 Aggressive Bot

File: `agents/aggressive_bot.py`

Decision priorities:

1. Target lowest HP enemy if visible.
2. Move toward target until in range.
3. Basic attack when off cooldown.
4. Use class ability when in range.
5. Ignore low HP unless extremely close to death.

Expected metrics:

- high damage,
- high deaths,
- low average distance to enemies.

#### 12.3.3 Defensive Bot

File: `agents/defensive_bot.py`

Decision priorities:

1. If HP below threshold, move away from nearest enemy.
2. Attack only when safe and in range.
3. Maintain distance from enemies.
4. Prefer moving toward ally if isolated.

Expected metrics:

- lower damage,
- higher survival,
- higher retreat frequency.

#### 12.3.4 Kiter Bot

File: `agents/kiter_bot.py`

Decision priorities:

1. Select nearest enemy within attack range.
2. If enemy too close, move away.
3. If enemy too far, move toward until just inside range.
4. Attack whenever in range and cooldown ready.

Expected metrics:

- maintains distance near attack range,
- good ranged DPS behavior,
- avoids tank range.

#### 12.3.5 Protector Bot

File: `agents/protector_bot.py`

Decision priorities:

1. Identify ally with lowest HP or nearest threat.
2. Move toward threatened ally.
3. Target enemy closest to threatened ally.
4. Attack enemy threatening ally.
5. Avoid chasing enemies away from ally.

Expected metrics:

- low average ally distance,
- high attacks against ally threats,
- lower ally deaths.

### 12.4 Baseline Validation

Each baseline bot must have:

1. unit tests for valid action output,
2. integration match against random bot,
3. replay sample,
4. metric signature check confirming expected behavior differences.

---

## 13. RL Environment Specification

### 13.1 Gymnasium Wrapper

File: `envs/gym_env.py`

```python
class CombatRLGymEnv(gymnasium.Env):
    metadata = {"render_modes": [None, "human", "rgb_array"], "render_fps": 30}

    def __init__(self, env_config: EnvironmentConfig): ...
    def reset(self, *, seed: int | None = None, options: dict | None = None): ...
    def step(self, action: int): ...
    def render(self): ...
    def close(self): ...
```

### 13.2 Reset Contract

`reset()` must:

1. initialize RNG with provided seed,
2. create fresh `MatchState`,
3. reset controlled and scripted policies,
4. return initial observation and info dict.

Return signature:

```python
observation, info = env.reset(seed=seed)
```

Info must include:

```python
{
    "match_id": str,
    "seed": int,
    "controlled_agent_id": str,
    "scenario_id": str
}
```

### 13.3 Step Contract

`step(action)` must:

1. decode controlled agent action,
2. obtain scripted actions for other agents,
3. advance simulator by `decision_interval_ticks`,
4. compute reward breakdown for controlled agent,
5. return observation, reward, terminated, truncated, info.

Return signature:

```python
observation, reward, terminated, truncated, info = env.step(action)
```

### 13.4 Termination and Truncation

| Condition | `terminated` | `truncated` |
|---|---:|---:|
| Win/loss by elimination | True | False |
| Controlled agent death but match continues | Configurable; default False | False |
| Max ticks reached | False | True |
| Invariant failure | False | True with error info |

### 13.5 PPO Compatibility Requirements

The Gymnasium env must expose:

```python
observation_space = gymnasium.spaces.Box(low=-1.0, high=1.0, shape=(OBS_DIM,), dtype=np.float32)
action_space = gymnasium.spaces.Discrete(N_ACTIONS)
```

Observation values in `[0,1]` are allowed inside Box `[-1,1]`.

### 13.6 Vectorization Strategy

MVP training uses SB3 `DummyVecEnv` first. After environment correctness is stable, use `SubprocVecEnv`.

Rules:

1. Every vectorized env must receive a unique seed.
2. Replay capture disabled by default in vectorized training.
3. Evaluation envs must be separate from training envs.

---

## 14. RL Training System

### 14.1 Training Pipeline

File: `training/train_ppo.py`

Pipeline order:

1. Load training config.
2. Create vectorized training environments.
3. Create separate evaluation environment.
4. Initialize PPO model.
5. Register callbacks for evaluation and checkpointing.
6. Train for configured timesteps.
7. Save final checkpoint.
8. Run post-training evaluation suite.
9. Save metrics and sample replays.

### 14.2 PPO Baseline Hyperparameters

Initial baseline:

```yaml
algorithm: PPO
policy: MlpPolicy
total_timesteps: 250000
n_envs: 8
n_steps: 512
batch_size: 256
n_epochs: 10
gamma: 0.99
gae_lambda: 0.95
learning_rate: 0.0003
clip_range: 0.2
ent_coef: 0.01
vf_coef: 0.5
max_grad_norm: 0.5
```

### 14.3 Checkpoint Structure

```text
artifacts/checkpoints/
  ppo_1v1_baseline/
    run_2026-05-23_001/
      model_final.zip
      best_model.zip
      config.yaml
      metrics.json
      eval_history.csv
      sample_replays/
```

### 14.4 Model Registry Metadata

```json
{
  "policy_id": "ppo_1v1_baseline_run_001",
  "algorithm": "PPO",
  "checkpoint_path": "artifacts/checkpoints/.../best_model.zip",
  "env_config_path": "configs/env/mvp_1v1.yaml",
  "training_config_path": "configs/training/ppo_1v1_baseline.yaml",
  "observation_schema_version": "1.0",
  "action_schema_version": "1.0",
  "total_timesteps": 250000,
  "created_at_utc": "..."
}
```

### 14.5 Training Progression Stages

| Stage | Scenario | Opponents | Goal |
|---|---|---|---|
| `RL-001` | 1v1 ranged vs random | Random | Learn attack basics |
| `RL-002` | 1v1 ranged vs aggressive | Aggressive | Learn spacing/survival |
| `RL-003` | 1v1 tank vs random | Random | Learn engagement |
| `RL-004` | 2v2 controlled ranged + scripted tank | Aggressive pair | Learn team context |
| `RL-005` | 2v2 role-specific training | Mixed heuristics | Learn robust behavior |

### 14.6 Evaluation During Training

Every evaluation interval:

1. Run at least 20 deterministic evaluation episodes.
2. Use fixed evaluation seed list.
3. Log mean reward and win rate.
4. Save best model by win rate first, mean reward second.
5. Save one sample replay from best checkpoint.

---

## 15. Multi-Agent Training Architecture

### 15.1 Implementation Progression Order

1. Single controlled agent with scripted teammate/opponents.
2. Role-specific policy trained with fixed scripted partners.
3. Shared team policy controlling same-team agents.
4. PettingZoo parallel environment wrapper.
5. Self-play with checkpoint opponent pool.
6. Centralized training / decentralized execution experiments.
7. RLlib integration if needed.

### 15.2 Shared Policy System

Shared policy means one model controls multiple agents of compatible role or team. Each agent receives its own observation and outputs its own action.

MVP does not require shared policy. Post-MVP may add shared policy for same role.

### 15.3 Role-Specific Policies

Role policies:

| Policy ID | Controls |
|---|---|
| `policy_tank_v1` | Tank agents |
| `policy_ranged_dps_v1` | Ranged DPS agents |
| `policy_support_v1` | Support agents, future |

### 15.4 Centralized Training / Decentralized Execution

Deferred until advanced stage.

Contract:

1. Training may use global state.
2. Inference must use per-agent observations only unless explicitly flagged.
3. Replay and evaluation must identify whether policy used centralized information.

### 15.5 Self-Play Opponent Pools

Opponent pool entry:

```json
{
  "policy_id": "ppo_2v2_checkpoint_100k",
  "checkpoint_path": "...",
  "rating": 1020.0,
  "added_at_timestep": 100000,
  "selection_weight": 0.25
}
```

Selection strategy progression:

1. Latest checkpoint only.
2. Uniform sample from last N checkpoints.
3. Weighted sample by rating gap.
4. League/tournament system.

---

## 16. Behavior Profile System

### 16.1 Profile Purpose

Behavior profiles modify tactical decision-making at inference time. They must not retrain the policy and must not directly override simulator rules.

### 16.2 Canonical Axes

| Axis | Range | High Value Means | Expected Metric Impact |
|---|---:|---|---|
| `aggression` | `[0,1]` | Engage/chase/attack more often | Higher damage, lower survival |
| `caution` | `[0,1]` | Retreat earlier, avoid danger | Higher survival, lower damage |
| `cohesion` | `[0,1]` | Stay near allies | Lower ally distance |
| `protectiveness` | `[0,1]` | Prioritize threats to allies | Fewer ally deaths, more peel actions |
| `focus_fire` | `[0,1]` | Prefer ally-selected targets | Higher shared target rate |
| `greed` | `[0,1]` | Chase low-HP enemies | More eliminations, more overextension |
| `spacing` | `[0,1]` | Maintain ideal range | Better kiting metrics |
| `objective_bias` | `[0,1]` | Prioritize objective zone | Future objective-control metrics |

### 16.3 Profile YAML Example

```yaml
profile_schema_version: "1.0"
profile_id: aggressive
aggression: 0.90
caution: 0.20
cohesion: 0.35
protectiveness: 0.25
focus_fire: 0.60
greed: 0.75
spacing: 0.30
objective_bias: 0.20
notes: "High-damage profile that accepts risky fights."
```

### 16.4 Modulation Methods

Allowed methods:

1. **Action reranking:** score top candidate actions and choose highest profile-adjusted score.
2. **Action masking:** suppress actions inconsistent with hard profile constraints.
3. **Target-priority weighting:** adjust target scores before selecting target intent.
4. **Utility blending:** combine heuristic utility scores with policy preferences.
5. **Policy conditioning:** future method where profile vector is appended to observation.

### 16.5 MVP Modulation Contract

MVP must implement action reranking for heuristic agents and optional wrapper around RL policy outputs.

```python
def rerank_actions(
    candidate_actions: list[int],
    base_scores: np.ndarray,
    state: MatchState,
    agent_id: str,
    profile: BehaviorProfile,
    action_codec: ActionCodec,
) -> int:
    ...
```

### 16.6 Utility Weighting Examples

Aggression adds score to:

- `move_toward_target`,
- `basic_attack`,
- targeting `lowest_hp_enemy`.

Caution adds score to:

- `move_away_from_danger`,
- `hold_position` when unsafe,
- avoiding attack if heavily outnumbered.

Cohesion adds score to:

- `move_toward_ally`,
- avoiding chase when ally distance is high.

Protectiveness adds score to:

- targeting enemies near low-HP allies,
- moving toward threatened allies.

### 16.7 Profile Validation Metrics

Every profile comparison must report:

| Metric | Expected Difference |
|---|---|
| `avg_damage_dealt` | Aggressive > Defensive |
| `avg_survival_ticks` | Defensive > Aggressive |
| `avg_distance_to_ally` | Protective/Cohesive < Aggressive |
| `retreat_action_rate` | Defensive > Aggressive |
| `low_hp_chase_rate` | Greedy > Defensive |
| `shared_target_rate` | Focus-fire > Default |

---

## 17. NLP Command System

### 17.1 Architecture

Natural language is converted to `BehaviorProfile` only.

```text
User command
  -> NLP parser
  -> Structured profile candidate
  -> Pydantic validation
  -> bounded profile
  -> behavior modulation layer
  -> action reranking / policy conditioning
```

### 17.2 Forbidden Behavior

The NLP system must not:

1. directly call `env.step(action)`,
2. output raw action IDs,
3. mutate simulator state,
4. bypass profile validation,
5. create new unsupported schema fields silently,
6. execute arbitrary code.

### 17.3 Parser Interface

File: `nlp/parser.py`

```python
def parse_command_to_profile(
    command: str,
    base_profile: BehaviorProfile | None = None,
) -> BehaviorProfileParseResult:
    ...
```

```python
class BehaviorProfileParseResult(BaseModel):
    success: bool
    command: str
    profile: BehaviorProfile | None
    errors: list[str]
    unsupported_requests: list[str]
    parser_source: Literal["rules", "llm", "fallback"]
```

### 17.4 Structured Output Contract

LLM output must be JSON only:

```json
{
  "profile_id": "generated_aggressive_protective",
  "aggression": 0.82,
  "caution": 0.45,
  "cohesion": 0.65,
  "protectiveness": 0.78,
  "focus_fire": 0.70,
  "greed": 0.55,
  "spacing": 0.50,
  "objective_bias": 0.20,
  "notes": "Aggressive profile that still protects low-health allies."
}
```

### 17.5 Validation Rules

1. Missing axes are filled from base profile or default profile.
2. Values below `0` clamp to `0` only if parser is trusted; otherwise reject.
3. Values above `1` clamp to `1` only if parser is trusted; otherwise reject.
4. Unsupported commands are returned in `unsupported_requests`.
5. Dangerous requests are rejected with `success=false`.

### 17.6 Rule-Based Fallback

File: `nlp/fallback_rules.py`

Keyword mapping examples:

| Keywords | Axis Changes |
|---|---|
| `aggressive`, `attack`, `push` | `aggression += 0.25`, `caution -= 0.10` |
| `defensive`, `safe`, `survive` | `caution += 0.30`, `aggression -= 0.15` |
| `protect`, `peel`, `guard` | `protectiveness += 0.35`, `cohesion += 0.15` |
| `kite`, `keep distance` | `spacing += 0.35`, `caution += 0.10` |
| `focus`, `same target` | `focus_fire += 0.35` |
| `chase`, `finish` | `greed += 0.25` |

---

## 18. Evaluation Framework

### 18.1 Evaluation Architecture

Evaluation system components:

| Component | File | Responsibility |
|---|---|---|
| Metrics computer | `evaluation/metrics.py` | Derive metrics from replay/events. |
| Benchmark suite | `evaluation/benchmark_suite.py` | Run policy matchups across seeds. |
| Aggregator | `evaluation/aggregate.py` | Aggregate per-match results. |
| Reports | `evaluation/reports.py` | Generate JSON/CSV/plots. |

### 18.2 Benchmark Suite Contract

```python
class BenchmarkSuite:
    def run(
        self,
        scenario_config: SimulationConfig,
        policy_specs: list[PolicySpec],
        seeds: list[int],
        profiles: list[BehaviorProfile] | None = None,
    ) -> EvaluationResult:
        ...
```

### 18.3 Core Metrics

#### Combat Metrics

| Metric | Definition |
|---|---|
| `win_rate` | wins / matches |
| `avg_damage_dealt` | average damage by controlled agent/team |
| `avg_damage_taken` | average damage received |
| `avg_eliminations` | average kills credited |
| `avg_deaths` | average deaths |
| `damage_per_survival_tick` | damage dealt / alive ticks |

#### Positioning Metrics

| Metric | Definition |
|---|---|
| `avg_distance_to_nearest_enemy` | mean distance each tick |
| `avg_distance_to_ally` | mean ally distance each tick |
| `time_in_attack_range_rate` | fraction of ticks with target in range |
| `time_in_enemy_threat_range_rate` | fraction of ticks inside enemy range |
| `center_control_rate` | fraction of ticks near center/objective |

#### Teamwork Metrics

| Metric | Definition |
|---|---|
| `shared_target_rate` | fraction of combat actions targeting same enemy as ally |
| `ally_peel_rate` | attacks against enemy threatening ally |
| `ally_survival_ticks` | teammate alive duration |
| `cohesion_score` | inverse normalized ally distance |

#### Profile-Difference Metrics

| Metric | Definition |
|---|---|
| `profile_damage_delta` | damage difference vs default profile |
| `profile_survival_delta` | survival difference vs default profile |
| `profile_spacing_delta` | spacing difference vs default profile |
| `profile_behavior_separation_score` | aggregate normalized difference across key profile metrics |

### 18.4 Statistical Comparison

For MVP:

1. Run at least 30 seeds per comparison.
2. Report mean and standard deviation.
3. Use bootstrap confidence intervals if implemented.
4. Avoid strong claims from fewer than 20 matches.

---

## 19. Frontend System Specification

### 19.1 Frontend Responsibilities

Frontend must:

1. load replay metadata,
2. render replay timeline,
3. show match metrics,
4. allow profile selection,
5. show parsed NLP profile,
6. compare two replays side-by-side,
7. display charts for evaluation results.

Frontend must not:

1. compute simulator state transitions,
2. train RL policies,
3. mutate replay data,
4. bypass backend validation for NLP profiles.

### 19.2 Backend API Requirements

Required endpoints post-MVP:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/replays` | List available replays |
| `GET` | `/api/replays/{id}/metadata` | Load metadata |
| `GET` | `/api/replays/{id}/frames` | Stream/load frames |
| `GET` | `/api/evaluations` | List evaluation results |
| `GET` | `/api/evaluations/{id}` | Load evaluation result |
| `POST` | `/api/commands/parse` | Parse language command to profile |
| `POST` | `/api/matches/run` | Optional: run local match with profile |

### 19.3 Replay Viewer UI Contract

Required UI components:

| Component | Responsibility |
|---|---|
| `ReplayViewer` | Canvas playback of frames |
| `TimelineControls` | Play/pause/speed/scrub |
| `MetricsPanel` | Display selected replay metrics |
| `ProfileInspector` | Show behavior axes |
| `CommandInput` | Submit language command |
| `ComparisonView` | Side-by-side replay/metric comparison |

---

## 20. Testing Strategy

### 20.1 Unit Tests

Required unit tests:

| Test File | Assertions |
|---|---|
| `test_geometry.py` | distance, normalization, clamp, collision helpers |
| `test_actions.py` | encode/decode roundtrip, masks, fallback |
| `test_rewards.py` | reward components and total sum |
| `test_profiles.py` | schema bounds, profile loading, modulation effects |

### 20.2 Integration Tests

| Test File | Assertions |
|---|---|
| `test_sim_determinism.py` | same seed/actions produce same final state |
| `test_replay_roundtrip.py` | saved replay loads and validates |
| `test_gym_env_contract.py` | reset/step signatures, spaces, no NaNs |
| `test_heuristic_matches.py` | bots produce valid complete matches |

### 20.3 RL Sanity Tests

| Test | Purpose |
|---|---|
| Random policy rollout | Environment does not crash for 100 episodes |
| Short PPO smoke | PPO can train for small timesteps without NaNs |
| Reward sign test | Winning produces higher return than losing scripted trajectory |
| Overfit tiny scenario | Policy can improve in trivial scenario |

### 20.4 Replay Validation Tests

Required assertions:

1. metadata exists,
2. frames are sorted,
3. frame ticks are monotonic,
4. final frame agrees with summary,
5. all agent states validate,
6. event ticks exist within frame tick range.

### 20.5 Determinism Test Pattern

```python
def test_same_seed_same_actions_same_result():
    result_a = run_match_with_fixed_actions(seed=123, actions=FIXED_ACTIONS)
    result_b = run_match_with_fixed_actions(seed=123, actions=FIXED_ACTIONS)
    assert result_a.final_state_hash == result_b.final_state_hash
```

---

## 21. Debugging Infrastructure

### 21.1 Logging Levels

| Level | Use |
|---|---|
| `DEBUG` | Per-tick action/target details during small matches |
| `INFO` | Match start/end, training progress, evaluation summary |
| `WARNING` | Invalid actions, fallback usage, unusual metric anomalies |
| `ERROR` | Invariant failures, serialization failures, training crash |

### 21.2 State Inspection Tools

Required scripts:

| Script | Purpose |
|---|---|
| `scripts/run_match.py` | Run one match and save replay |
| `scripts/render_replay.py` | Render replay locally |
| `scripts/validate_replay.py` | Validate replay schema/invariants |
| `scripts/compare_profiles.py` | Run profile comparison suite |
| `scripts/evaluate_policy.py` | Evaluate checkpoint across seeds |

### 21.3 Common Failure Diagnosis

| Symptom | Likely Cause | Debug Workflow |
|---|---|---|
| Agent jitters | Decision rate too high or action flip-flop | Inspect action event feed; add action repeat. |
| Agent never attacks | Range too short, target invalid, cooldown bug | Enable attack range overlay and combat events. |
| PPO reward NaNs | Observation NaN or reward explosion | Run observation validation and reward component logs. |
| Policy camps | Reward too survival-heavy | Inspect time penalty, objective pressure, damage rewards. |
| Replay desync | Renderer recomputing or missing frames | Validate replay frame/event ordering. |
| Profiles look identical | Modulation weights too weak | Compare action distributions and profile metrics. |

### 21.4 Debugging Priorities

Order when diagnosing failures:

1. Validate schemas.
2. Validate deterministic simulator.
3. Validate replay output.
4. Watch replay with overlays.
5. Inspect event logs.
6. Inspect reward breakdowns.
7. Only then inspect neural policy behavior.

---

## 22. Incremental Build Order

### 22.1 Phase `P0`: Repository and Configuration Foundation

Dependencies: none  
Downstream consumers: all phases  

Implementation targets:

- `pyproject.toml`
- `src/combatrl/__init__.py`
- `src/combatrl/core/`
- `src/combatrl/schemas/configs.py`
- `configs/env/mvp_2v2_elimination.yaml`
- `tests/unit/test_geometry.py`

Tasks:

- [ ] Create Python package structure.
- [ ] Configure `ruff`, `pytest`, and optional `mypy`.
- [ ] Implement core type aliases.
- [ ] Implement deterministic RNG wrapper.
- [ ] Implement basic geometry helpers.
- [ ] Create initial simulation config schema.

Tests to pass:

- [ ] Import package.
- [ ] Load config YAML.
- [ ] Validate geometry helpers.
- [ ] Validate RNG deterministic output.

Completion criteria:

- `pytest` runs successfully.
- Config loads into `SimulationConfig`.

### 22.2 Phase `P1`: Core Simulator State

Dependencies: `P0`  
Downstream consumers: replay, agents, RL wrapper  

Files to create:

- `schemas/agent_state.py`
- `schemas/match_state.py`
- `sim/engine.py`
- `sim/invariants.py`
- `scripts/run_match.py`

Tasks:

- [ ] Define `AgentState`.
- [ ] Define `MatchState`.
- [ ] Initialize match from config.
- [ ] Implement tick progression without combat.
- [ ] Implement invariant checks.

Tests:

- [ ] State initializes with correct team/role IDs.
- [ ] Tick increments deterministically.
- [ ] Invariants catch invalid HP/position.

Completion criteria:

- Running `scripts/run_match.py` produces a terminal timeout with no crashes.

### 22.3 Phase `P2`: Movement, Combat, and Win Conditions

Dependencies: `P1`  
Downstream consumers: agents, replay, rewards  

Files:

- `sim/movement.py`
- `sim/combat.py`
- `sim/cooldowns.py`
- `sim/targeting.py`
- `sim/win_conditions.py`
- `schemas/actions.py`

Tasks:

- [ ] Implement movement intents.
- [ ] Implement targeting helpers.
- [ ] Implement basic attacks.
- [ ] Implement cooldown decrement.
- [ ] Implement death resolution.
- [ ] Implement elimination win condition.

Tests:

- [ ] Agent moves toward target.
- [ ] Agent cannot move outside arena.
- [ ] Attack only damages in range.
- [ ] Cooldown prevents repeated attacks.
- [ ] Match ends when one team eliminated.

Completion criteria:

- Scripted fixed actions can produce damage, death, and winner.

### 22.4 Phase `P3`: Replay Writer and Debug Renderer

Dependencies: `P2`  
Downstream consumers: evaluation, frontend, debugging  

Files:

- `schemas/replay.py`
- `replay/writer.py`
- `replay/reader.py`
- `replay/validators.py`
- `renderer/pygame_renderer.py`
- `scripts/render_replay.py`
- `scripts/validate_replay.py`

Tasks:

- [ ] Create replay schema.
- [ ] Write metadata, frames, events.
- [ ] Read replay files.
- [ ] Validate replay files.
- [ ] Render arena and agents.
- [ ] Render HP bars and target lines.

Tests:

- [ ] Replay roundtrip validates.
- [ ] Frame ticks are monotonic.
- [ ] Renderer smoke test loads a replay.

Completion criteria:

- A match can be saved and visually replayed.

### 22.5 Phase `P4`: Heuristic Baseline Agents

Dependencies: `P3`  
Downstream consumers: RL training, evaluation, profiles  

Files:

- `agents/base.py`
- `agents/random_bot.py`
- `agents/aggressive_bot.py`
- `agents/defensive_bot.py`
- `agents/kiter_bot.py`
- `agents/protector_bot.py`
- `agents/utility.py`

Tasks:

- [ ] Implement `AgentPolicy` protocol.
- [ ] Implement Random bot.
- [ ] Implement Aggressive bot.
- [ ] Implement Defensive bot.
- [ ] Implement Kiter bot.
- [ ] Implement Protector bot.
- [ ] Add bot matchup script.

Tests:

- [ ] Every bot returns valid actions.
- [ ] Bot matches complete without crash.
- [ ] Behavior metrics differ by bot.

Completion criteria:

- Replay clearly shows different bot behaviors.

### 22.6 Phase `P5`: Gymnasium Environment Wrapper

Dependencies: `P4`  
Downstream consumers: RL training  

Files:

- `schemas/observations.py`
- `schemas/rewards.py`
- `envs/action_codec.py`
- `envs/observation_builder.py`
- `envs/reward_builder.py`
- `envs/gym_env.py`
- `tests/integration/test_gym_env_contract.py`

Tasks:

- [ ] Implement action codec.
- [ ] Implement observation builder.
- [ ] Implement reward builder.
- [ ] Implement Gymnasium reset/step.
- [ ] Validate observation/action spaces.

Tests:

- [ ] `reset()` returns valid observation/info.
- [ ] `step()` returns valid Gymnasium tuple.
- [ ] Random rollout for 100 episodes has no crash.
- [ ] No observation NaNs.

Completion criteria:

- SB3 can instantiate the environment.

### 22.7 Phase `P6`: PPO Training Baseline

Dependencies: `P5`  
Downstream consumers: evaluation, behavior profiles  

Files:

- `training/train_ppo.py`
- `training/callbacks.py`
- `training/registry.py`
- `training/evaluate_checkpoint.py`
- `configs/training/ppo_1v1_baseline.yaml`

Tasks:

- [ ] Create vectorized env factory.
- [ ] Train PPO for short smoke test.
- [ ] Add checkpoint saving.
- [ ] Add evaluation callback.
- [ ] Save sample replay from evaluated checkpoint.

Tests:

- [ ] Short PPO smoke completes.
- [ ] Checkpoint file exists.
- [ ] Evaluation JSON exists.

Completion criteria:

- Trained policy beats random baseline in a simple scenario.

### 22.8 Phase `P7`: 2v2 Team Environment

Dependencies: `P6`  
Downstream consumers: behavior profiles, evaluation  

Files:

- `configs/env/mvp_2v2_elimination.yaml`
- updates to observation builder,
- updates to reward builder,
- integration tests for 2v2.

Tasks:

- [ ] Support controlled agent with scripted teammate.
- [ ] Add teammate features to observation.
- [ ] Add ally death penalty.
- [ ] Add 2v2 evaluation scenario.

Tests:

- [ ] 2v2 matches terminate correctly.
- [ ] Observations include ally/enemy slots.
- [ ] Team outcome reward works.

Completion criteria:

- 2v2 replay with trainable or scripted controlled agent works.

### 22.9 Phase `P8`: Behavior Profiles

Dependencies: `P7`  
Downstream consumers: NLP, frontend, profile evaluation  

Files:

- `schemas/profiles.py`
- `profiles/loader.py`
- `profiles/validators.py`
- `profiles/modulation.py`
- `configs/profiles/*.yaml`
- `scripts/compare_profiles.py`

Tasks:

- [ ] Define profile schema.
- [ ] Load profiles from YAML.
- [ ] Apply action reranking.
- [ ] Run default/aggressive/defensive/protective comparisons.
- [ ] Compute profile difference metrics.

Tests:

- [ ] Invalid profile rejected.
- [ ] Profile values bounded.
- [ ] Aggressive profile increases attack rate vs defensive.
- [ ] Protective profile decreases ally distance.

Completion criteria:

- Same scenario produces visibly and measurably different behavior by profile.

### 22.10 Phase `P9`: Evaluation Framework

Dependencies: `P8`  
Downstream consumers: dashboard, project reporting  

Files:

- `schemas/evaluation.py`
- `evaluation/metrics.py`
- `evaluation/benchmark_suite.py`
- `evaluation/aggregate.py`
- `evaluation/reports.py`
- `scripts/evaluate_policy.py`

Tasks:

- [ ] Compute combat metrics.
- [ ] Compute positioning metrics.
- [ ] Compute teamwork metrics.
- [ ] Aggregate across seeds.
- [ ] Export JSON and CSV.

Tests:

- [ ] Metrics computed from known replay.
- [ ] Aggregates match manual values.
- [ ] Evaluation suite runs fixed seed list.

Completion criteria:

- Policies/profiles can be compared across 30+ seeds with saved metrics.

### 22.11 Phase `P10`: NLP Command Parser

Dependencies: `P8`  
Downstream consumers: frontend/backend  

Files:

- `nlp/parser.py`
- `nlp/fallback_rules.py`
- `nlp/validation.py`
- `nlp/prompts.py`

Tasks:

- [ ] Implement rule-based parser.
- [ ] Implement optional LLM structured-output parser.
- [ ] Validate into `BehaviorProfile`.
- [ ] Return unsupported requests explicitly.

Tests:

- [ ] "play aggressively" increases aggression.
- [ ] "protect ally" increases protectiveness.
- [ ] unsupported commands do not crash.
- [ ] output always validates or returns errors.

Completion criteria:

- Text command creates valid profile that changes behavior in simulation.

### 22.12 Phase `P11`: Backend and Frontend Dashboard

Dependencies: `P9`, `P10`  
Downstream consumers: portfolio demo  

Files:

- `backend/app.py`
- `backend/routes_replays.py`
- `backend/routes_metrics.py`
- `backend/routes_commands.py`
- `frontend/src/components/*`

Tasks:

- [ ] Serve replay list and frames.
- [ ] Serve evaluation metrics.
- [ ] Add command parsing endpoint.
- [ ] Build replay viewer.
- [ ] Build metrics panel.
- [ ] Build profile inspector.
- [ ] Build comparison view.

Tests:

- [ ] API route smoke tests.
- [ ] Frontend loads sample replay.
- [ ] Command input displays parsed profile.

Completion criteria:

- Browser demo can run or inspect replays and compare profiles.

### 22.13 Phase `P12`: Post-MVP Mechanics

Dependencies: `P11`  
Downstream consumers: research-grade systems  

Implementation order:

1. Support/healer role.
2. Objective-control mode.
3. Directional abilities.
4. PettingZoo wrapper.
5. Self-play opponent pool.
6. Advanced MARL.

Completion criteria:

- Each added mechanic must include replay, metrics, tests, and profile/evaluation compatibility.

---

## 23. Autonomous Execution Rules

### 23.1 Required Rules for Future LLM Implementers

1. Never break deterministic simulation.
2. Never couple renderer to simulator internals.
3. Never bypass replay logging for match behavior changes.
4. Never modify public schemas without updating this document.
5. Never introduce NLP direct action control.
6. Never add advanced features before their dependency phases are complete.
7. Always add tests for new simulator mechanics.
8. Always run replay validation after changing simulation logic.
9. Always preserve existing replay compatibility unless intentionally bumping schema version.
10. Always make fallback behavior deterministic.

### 23.2 Refactor Rules

A refactor is allowed only if:

1. existing tests pass before and after,
2. public interfaces stay unchanged or versioned,
3. replay compatibility is checked,
4. functionality remains demoable,
5. no lower-level module imports a higher-level module.

### 23.3 Migration Rules

If a schema changes:

1. bump schema version,
2. add migration note,
3. update validators,
4. update tests,
5. preserve loader for previous version if feasible.

---

## 24. Future Expansion Contracts

### 24.1 Support / Healer Role

Stable interfaces:

- `AgentState.role`
- `ActionDefinition.combat_intent`
- `BehaviorProfile.protectiveness`
- `RewardBreakdown.components`

Expected additions:

- healing events,
- ally-targeting actions,
- healing metrics,
- support positioning heuristics.

Do not add support until tank/ranged 2v2 behavior profiles are stable.

### 24.2 Objective-Control Mode

Stable interfaces:

- `SimulationConfig.win_condition`
- `MatchState.scoreboard` via replay frame
- `BehaviorProfile.objective_bias`

Expected additions:

- objective zone state,
- capture scoring,
- objective metrics,
- center-control rewards.

### 24.3 Fog of War

Deferred.

Required before implementation:

1. visibility system,
2. partial observation schema version,
3. hidden-state replay policy,
4. renderer support for observer vs agent view.

### 24.4 Skillshots

Deferred.

Initial implementation must use discrete direction bins:

```text
N, NE, E, SE, S, SW, W, NW
```

Do not implement continuous aiming until discrete skillshots are stable.

### 24.5 Larger Teams

Before 3v3 or 5v5:

1. observation slot system must generalize,
2. replay performance must be acceptable,
3. metrics must aggregate by role,
4. heuristic bots must scale.

### 24.6 Advanced MARL

Before PettingZoo/RLlib:

1. Gymnasium single-agent wrapper stable,
2. 2v2 scenario stable,
3. evaluation suite stable,
4. checkpoint registry stable.

---

## 25. Anti-Patterns and Failure Modes

### 25.1 Overengineering Infrastructure

Symptom:

- Docker, Redis, Postgres, distributed training added before simulator works.

Consequence:

- Slow iteration and no useful behavior.

Prevention:

- Keep MVP local, file-based, and headless.

### 25.2 Frontend-First Development

Symptom:

- Beautiful dashboard with unreliable simulation.

Consequence:

- Demo cannot support meaningful claims.

Prevention:

- Build replay and metrics before browser UI.

### 25.3 Reward Overdesign

Symptom:

- Dozens of reward terms before basic learning.

Consequence:

- Impossible to debug policy behavior.

Prevention:

- Start with simple damage/survival/win rewards.

### 25.4 Simulation/Rendering Coupling

Symptom:

- Match only runs when Pygame/browser is active.

Consequence:

- Training blocked and tests brittle.

Prevention:

- Renderer reads replay frames only.

### 25.5 Uncontrolled Action Space

Symptom:

- Continuous movement/aiming added before policy learns tactics.

Consequence:

- RL spends capacity learning mechanics instead of teamwork.

Prevention:

- Use discrete tactical intents first.

### 25.6 Invalid Replay Design

Symptom:

- Replays omit config/seed/events or cannot be validated.

Consequence:

- Debugging and frontend become unreliable.

Prevention:

- Use required metadata/frames/events structure from Section 10.

### 25.7 Architecture Drift

Symptom:

- Future code imports across forbidden boundaries.

Consequence:

- Modules become hard to test independently.

Prevention:

- Enforce import boundaries in review and optional lint rules.

---

## 26. Definition of Completion

### 26.1 MVP Completion

MVP is complete when all conditions are true:

- [ ] Deterministic 2v2 elimination simulator exists.
- [ ] Tank and ranged DPS roles exist.
- [ ] Movement, attacks, cooldowns, deaths, and win conditions work.
- [ ] Heuristic bots exist: Random, Aggressive, Defensive, Kiter, Protector.
- [ ] Replays are saved and validated.
- [ ] Local replay renderer displays matches with HP bars and overlays.
- [ ] Gymnasium wrapper passes reset/step contract tests.
- [ ] PPO baseline trains without NaNs.
- [ ] PPO baseline beats random in a simple scenario.
- [ ] Behavior profiles load from YAML.
- [ ] Behavior profiles cause measurable behavior differences.
- [ ] Evaluation framework reports combat, positioning, and teamwork metrics.
- [ ] All MVP tests pass.

### 26.2 Post-MVP Completion

Post-MVP is complete when all MVP items plus these are true:

- [ ] NLP command parser maps text to validated profiles.
- [ ] Frontend replay viewer loads replay files.
- [ ] Metrics dashboard displays evaluation results.
- [ ] Side-by-side replay/profile comparison works.
- [ ] Support/healer role exists with healing metrics.
- [ ] Objective-control mode exists.
- [ ] Project can produce a polished demo recording.

### 26.3 Research-Grade Completion

Research-grade completion is achieved when:

- [ ] Role-specific policies are trained and evaluated.
- [ ] Self-play opponent pool exists.
- [ ] Curriculum learning scenarios exist.
- [ ] PettingZoo parallel wrapper exists.
- [ ] Multi-agent evaluation tournament exists.
- [ ] Behavior-conditioned policy experiments are implemented.
- [ ] Statistical comparisons across policies/profiles are reported.
- [ ] Architecture remains compatible with deterministic replay and evaluation contracts.

### 26.4 Final Portfolio-Worthy Result

The final project should demonstrate:

1. a polished tactical combat sandbox,
2. real RL training and evaluation,
3. interpretable multi-agent behavior,
4. language-driven tactical behavior control,
5. replay-based debugging and visualization,
6. quantitative metrics proving behavior changes,
7. clean engineering architecture suitable for further research.
