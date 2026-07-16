# CombatRL Task Tracker

This file is the canonical tracker for unfinished work and future ambitions.
Other documents provide design context, historical phase notes, and limitations,
but task status must be updated here.

```yaml
tracker_version: 1
last_updated: 2026-07-16
status_values: [in_progress, not_started, blocked, done, cancelled]
priority_values: [P0, P1, P2, P3]
scope_values: [scoped, partially_scoped, unscoped]
```

## Maintenance Rules

1. Keep each task ID stable. Never reuse an ID.
2. Update the existing task instead of creating a duplicate.
3. Use exactly one value from each controlled vocabulary above.
4. Keep `Status`, `Priority`, and `Scope` as separate fields.
5. `P0` is urgent/correctness-critical, `P1` is the next meaningful work,
   `P2` is important but non-blocking, and `P3` is long-term research scope.
6. A task may be marked `done` only when every `Done when` item is satisfied.
7. When completing a task, set `Status: done`, add `Completed: YYYY-MM-DD`,
   add concise verification evidence, and move it to `Completed Tasks`.
8. When adding a task, use the next unused ID in the appropriate range:
   `CRL-001` through `CRL-099` for active or near-term work and `CRL-101`
   onward for unscoped ambitions.
9. Do not convert explicit non-goals into tasks without a deliberate scope
   decision. In particular, replay rendering must not recompute simulation,
   and NLP must not directly mutate simulator state or emit raw actions.
10. Update `last_updated` whenever task state or content changes.

## Task Index

| ID | Priority | Status | Scope | Title |
|---|---|---|---|---|
| CRL-001 | P1 | done | scoped | Harden replay viewer ingestion |
| CRL-002 | P1 | in_progress | scoped | Scope the P11 backend and dashboard |
| CRL-003 | P1 | in_progress | scoped | Improve training distribution robustness |
| CRL-004 | P1 | in_progress | scoped | Validate reward-shaping removal |
| CRL-005 | P2 | done | scoped | Improve teamwork intent and metrics |
| CRL-006 | P2 | done | scoped | Finish replay viewer product polish |
| CRL-007 | P2 | done | scoped | Automate browser viewer regression coverage |
| CRL-008 | P2 | in_progress | scoped | Profile large-replay performance |
| CRL-009 | P1 | not_started | scoped | Define local artifact catalog contracts |
| CRL-010 | P1 | not_started | scoped | Implement the read-only artifact API |
| CRL-011 | P2 | not_started | scoped | Build the experiment dashboard |
| CRL-101 | P2 | not_started | unscoped | Objective-control mode |
| CRL-102 | P2 | not_started | unscoped | Support/healer role |
| CRL-103 | P2 | not_started | unscoped | Pathfinding and richer arenas |
| CRL-104 | P3 | not_started | unscoped | Explicit targeting and skillshots |
| CRL-105 | P3 | not_started | unscoped | Advanced multi-agent RL |
| CRL-106 | P3 | not_started | unscoped | Live LLM profile translation service |
| CRL-107 | P3 | not_started | unscoped | Fog of war |

## Active And Incomplete Work

These tasks represent started subsystems, known gaps, or the next official
phase. Resolve these before expanding into lower-priority ambitions unless a
task is explicitly deprioritized.

### CRL-002: Scope the P11 backend and dashboard

- Status: `in_progress`
- Priority: `P1`
- Scope: `scoped`
- Area: `product/backend/frontend`
- Current state: P11 is the next roadmap phase. A replay-only frontend exists,
  but there is no backend, replay catalog, experiment browser, or full dashboard.
- Remaining work:
  - Obtain product approval for `docs/p11_backend_dashboard_scope.md`.
  - Begin CRL-009 only after the read-only local boundary is approved.
- Done when:
  - An approved P11 scope document and implementation plan exist.
  - Backend and frontend ownership boundaries are explicit.
  - Tasks derived from the plan have acceptance criteria and dependencies.
- Dependencies: CRL-001 should inform replay-related API requirements.
- Sources: `README.md` roadmap, `docs/phase_p10.md`, `docs/nlp.md`
- Progress:
  - The scope document defines users, workflows, FastAPI justification, API and
    ownership boundaries, artifact discovery, security, non-goals, tests, and
    delivery tasks CRL-009 through CRL-011.

### CRL-003: Improve training distribution robustness

- Status: `in_progress`
- Priority: `P1`
- Scope: `scoped`
- Area: `training/evaluation`
- Current state: The curriculum-trained ranged policy performs strongly on a
  narrow scenario with fixed spawns and limited opponent variation. The tank
  role is not comparably trained.
- Remaining work:
  - Train and evaluate the tank-controlled slot.
  - Inspect saved replay samples and document recurring ranged-policy failures.
  - Repeat learned-policy comparisons after a tank checkpoint exists.
- Done when:
  - Evaluation covers randomized spawns, mixed opponents, and both controlled roles.
  - Results include replay inspection and at least 30 fixed seeds per claim.
  - Performance and failure modes are documented without overstating generality.
- Dependencies: Existing curriculum and evaluation framework.
- Sources: `README.md` limitations, `docs/rl_training.md`
- Progress:
  - Added deterministic, arena-bounded team spawn translation and ranged/tank
    generalization configs.
  - Defined 30-seed, mixed-opponent, replay-sampling gates.
  - Ranged S5 randomized-spawn result: 26 wins, 4 timeouts, 0 losses.
  - Tank heuristic plumbing baseline: 30 wins but only 5.87 mean controlled
    damage; this does not satisfy the learned tank requirement.

### CRL-004: Validate reward-shaping removal

- Status: `in_progress`
- Priority: `P1`
- Scope: `scoped`
- Area: `training/rewards`
- Current state: Reward shaping remains enabled in the final training stage;
  evaluation metrics are shaping-independent, but sustained behavior under an
  annealed or sparse objective has not been demonstrated.
- Remaining work:
  - Run full-budget training for at least three seeds per stage.
  - Compare shaped, annealed, and canonical sparse checkpoints on fixed seeds.
  - Inspect action histograms and representative replays for regression.
- Done when:
  - The experiment is reproducible from committed configs and commands.
  - Results show whether combat behavior survives shaping reduction.
  - Findings and limitations are documented.
- Dependencies: CRL-003 may supply broader evaluation scenarios.
- Sources: `README.md` limitations, `docs/rl_training.md`
- Progress:
  - Added half, quarter, and sparse environment/training configs and a committed
    protocol.
  - The complete warm-start chain passed 1,024-timestep smoke runs. No behavior
    conclusion is claimed from those smoke artifacts.

### CRL-008: Profile large-replay performance

- Status: `in_progress`
- Priority: `P2`
- Scope: `scoped`
- Area: `frontend/replay/performance`
- Current state: Replay files are read and parsed fully in memory, which is
  appropriate for current artifacts but has no documented size budget.
- Remaining work:
  - Measure browser memory use and isolate Three.js scene rebuild cost.
  - Introduce streaming parsing, indexing, or a Web Worker only if measurements
    demonstrate a need.
- Done when:
  - Repeatable benchmark inputs and thresholds are documented.
  - Large replay behavior is measured on supported browsers.
  - Any optimization preserves replay fidelity and existing schema semantics.
- Dependencies: CRL-001.
- Sources: `docs/3d_replay_viewer.md`, `docs/replay_schema.md`
- Progress:
  - Added repeatable 20,000-line parse and 5,000-frame timeline budgets.
  - Edge browser regression enforces a five-second bundled-load budget.
  - Current measurements pass; no optimization was introduced.

### CRL-009: Define local artifact catalog contracts

- Status: `not_started`
- Priority: `P1`
- Scope: `scoped`
- Area: `backend/contracts`
- Current state: P11 has an implementation-ready scope but no catalog models or
  fixture-based contract tests.
- Remaining work:
  - Define opaque run/replay identifiers and validated response models.
  - Build empty, valid, corrupt, partial, and path-escape fixture trees.
  - Test stable ordering, diagnostics, root containment, and file allowlists.
- Done when:
  - Contract tests define all CRL-010 endpoint behavior without a running server.
  - No response exposes unrestricted host filesystem paths.
- Dependencies: CRL-002 approval.
- Sources: `docs/p11_backend_dashboard_scope.md`

### CRL-010: Implement the read-only artifact API

- Status: `not_started`
- Priority: `P1`
- Scope: `scoped`
- Area: `backend/api`
- Current state: No backend dependency or process exists.
- Remaining work:
  - Add the minimal FastAPI service defined by the approved P11 contract.
  - Bind to loopback, configure allowlisted roots, and expose read-only endpoints.
  - Add API integration tests over CRL-009 fixtures.
- Done when:
  - Health, run, metrics, replay manifest, and allowlisted file endpoints pass.
  - Traversal and out-of-root access are rejected.
- Dependencies: CRL-009.
- Sources: `docs/p11_backend_dashboard_scope.md`

### CRL-011: Build the experiment dashboard

- Status: `not_started`
- Priority: `P2`
- Scope: `scoped`
- Area: `frontend/dashboard`
- Current state: The frontend opens replays but has no experiment catalog UI.
- Remaining work:
  - Add empty/error/loading states, run filtering, metrics comparison, and replay handoff.
  - Preserve local directory import as a backend-independent workflow.
  - Add browser contract fixtures and accessibility coverage.
- Done when:
  - A user can browse validated local runs and open a catalog replay.
  - The UI does not start or mutate training, evaluation, or simulation.
- Dependencies: CRL-010.
- Sources: `docs/p11_backend_dashboard_scope.md`, `docs/3d_replay_viewer.md`

## Unscoped Ambitions

These are recognized future directions, not approved implementation plans.
Before coding, change `Scope` to `partially_scoped` or `scoped`, define explicit
non-goals, split large items into near-term tasks, and update the task index.

### CRL-101: Objective-control mode

- Status: `not_started`
- Priority: `P2`
- Scope: `unscoped`
- Area: `simulation/environment/evaluation`
- Ambition: Add objective zones and objective-aware policies, profiles,
  observations, rewards, replays, and metrics.
- Required scoping: Win conditions, deterministic resolution, schema changes,
  reward boundaries, tests, and migration strategy.
- Dependencies: Stable elimination-mode behavior must remain backward-compatible.
- Sources: `docs/CombatRL_Canonical_Project_Spec.md` section 24.2, `docs/profiles.md`

### CRL-102: Support/healer role

- Status: `not_started`
- Priority: `P2`
- Scope: `unscoped`
- Area: `simulation/agents/environment`
- Ambition: Implement the reserved support role with deterministic ally support
  behavior and complete observation, action, replay, renderer, and evaluation coverage.
- Required scoping: Ability semantics, targeting, cooldowns, balance assumptions,
  action-space compatibility, and tests.
- Dependencies: Likely CRL-104 for explicit ally targeting decisions.
- Sources: `docs/CombatRL_Canonical_Project_Spec.md` section 24.1, `docs/agents.md`

### CRL-103: Pathfinding and richer arenas

- Status: `not_started`
- Priority: `P2`
- Scope: `unscoped`
- Area: `simulation/geometry`
- Ambition: Add deterministic obstacle-aware movement and scenarios where arena
  geometry creates meaningful tactical choices.
- Required scoping: Navigation algorithm, collision semantics, determinism,
  observation impact, performance budgets, and replay compatibility.
- Dependencies: None identified; must not silently alter existing scenarios.
- Sources: `README.md` limitations, simulation config obstacle fields

### CRL-104: Explicit targeting and skillshots

- Status: `not_started`
- Priority: `P3`
- Scope: `unscoped`
- Area: `simulation/actions/agents`
- Ambition: Move beyond `ATTACK_NEAREST` with explicit target IDs and eventually
  deterministic directional or point-targeted skillshots.
- Required scoping: Action schema versioning, invalid-target behavior, Gymnasium
  encoding, bot APIs, observations, replay events, and renderer support.
- Dependencies: Foundational for richer support and combat abilities.
- Sources: `docs/agents.md`, `docs/CombatRL_Canonical_Project_Spec.md` section 24.4

### CRL-105: Advanced multi-agent RL

- Status: `not_started`
- Priority: `P3`
- Scope: `unscoped`
- Area: `environment/training/evaluation`
- Ambition: Explore PettingZoo, simultaneous multi-agent learning, shared team
  policies, centralized critics, self-play, opponent pools, larger teams, and
  advanced MARL only after simpler baselines justify the complexity.
- Required scoping: Research question, baseline, API choice, compute budget,
  reproducibility gates, opponent sampling, and evaluation protocol.
- Dependencies: CRL-003 and stable single-agent baselines; do not introduce
  RLlib or distributed infrastructure prematurely.
- Sources: `docs/evaluation.md`, `docs/rl_environment.md`,
  `docs/CombatRL_Canonical_Project_Spec.md` sections 24.5-24.6

### CRL-106: Live LLM profile translation service

- Status: `not_started`
- Priority: `P3`
- Scope: `unscoped`
- Area: `nlp/backend`
- Ambition: Expose the existing validated natural-language-to-profile translator
  through an optional live service without making the LLM a controller.
- Required scoping: Provider-neutral interface, structured outputs, timeouts,
  cost controls, privacy, deterministic fallback, and offline tests.
- Dependencies: CRL-002 backend scope.
- Sources: `docs/nlp.md`, `docs/phase_p10.md`
- Non-goal: Direct raw-action generation or simulator mutation from LLM output.

### CRL-107: Fog of war

- Status: `not_started`
- Priority: `P3`
- Scope: `unscoped`
- Area: `simulation/observations/rendering`
- Ambition: Add deterministic visibility and partial observability for research
  scenarios after full-observability baselines are mature.
- Required scoping: Visibility geometry, observation masking, hidden-state replay
  policy, renderer behavior, evaluation fairness, and compatibility.
- Dependencies: Richer arena geometry may depend on CRL-103.
- Sources: `docs/CombatRL_Canonical_Project_Spec.md` section 24.3

## Completed Tasks

### CRL-005: Improve teamwork intent and metrics

- Status: `done`
- Priority: `P2`
- Scope: `scoped`
- Area: `replay/evaluation`
- Completed: `2026-07-16`
- Final state:
  - `agent_action_selected` attack payloads include additive
    `target_intent_id` evidence without changing replay schema version `1.0`.
  - Shared-target and ally-peel metrics use explicit evidence and return `null`
    for older replays where intent is unavailable.
  - `teamwork_intent_evidence_rate` reports evidence coverage.
- Verification:
  - Simulator event, replay/evaluation, aggregation compatibility, and focused
    regression tests pass.
- Dependencies: Replay schema design review.
- Sources: `docs/evaluation.md`, `docs/replay_schema.md`

### CRL-007: Automate browser viewer regression coverage

- Status: `done`
- Priority: `P2`
- Scope: `scoped`
- Area: `frontend/testing`
- Completed: `2026-07-16`
- Final state:
  - Playwright runs through Yarn Plug'n'Play against local Microsoft Edge.
  - Scenarios cover bundled loading, directory fixture import, recoverable
    invalid input, playback shortcuts, accessible agent selection/follow, and a
    compact viewport.
  - Failures retain screenshots and DOM error context without cloud services or
    live simulation.
- Verification:
  - `corepack yarn test:browser`: 3 passed.
- Dependencies: CRL-001 and CRL-006.
- Sources: `docs/3d_replay_viewer.md`, `frontend/playwright.config.ts`

### CRL-001: Harden replay viewer ingestion

- Status: `done`
- Priority: `P1`
- Scope: `scoped`
- Area: `frontend/replay`
- Completed: `2026-06-19`
- Final state:
  - Users can select one local replay directory without an upload or backend.
  - Runtime validation reports missing files, malformed JSON/JSONL, unsupported
    schema versions, invalid fields, identity mismatches, count mismatches, and
    invalid frame/event ranges with file/line/field context.
  - Failed imports preserve the currently open replay and offer demo recovery.
- Done when:
  - A user can open an arbitrary valid CombatRL replay without modifying code.
  - Invalid replay input produces actionable errors and does not crash the UI.
  - Loader and validation tests cover success and failure paths.
- Verification:
  - Frontend test suite covers static and local loading, incomplete/duplicate
    directories, malformed JSONL, schema mismatch, invalid agents, and cross-file consistency.
  - The unchanged bundled replay remains compatible with the authoritative Python validator.
- Dependencies: None.
- Sources: `docs/3d_replay_viewer.md`, `docs/replay_schema.md`

### CRL-006: Finish replay viewer product polish

- Status: `done`
- Priority: `P2`
- Scope: `scoped`
- Area: `frontend/rendering`
- Completed: `2026-06-19`
- Final state:
  - Follow mode tracks the selected agent while preserving camera offset.
  - Playback, seeking, speed, camera, follow, range, and target controls have
    documented keyboard shortcuts and visible focus/pressed/disabled states.
  - Compact layouts use larger touch targets and scrollable control groups.
  - The scene is lazy-loaded; the initial chunk is separated from the Three.js
    renderer under a documented 560 kB minified budget.
  - Audio and richer effects remain deferred because current effects already
    communicate replay state without additional assets or controls.
- Done when:
  - Core controls are keyboard-accessible and usable at supported viewport sizes.
  - The production bundle warning is resolved or accepted with rationale.
  - Optional polish does not introduce live simulation or game-rule logic.
- Verification:
  - Shortcut mapping has unit coverage and TypeScript/build checks pass.
  - Renderer code splitting is visible in production build output.
- Dependencies: CRL-001.
- Sources: `docs/3d_replay_viewer.md`

## New Task Template

```markdown
### CRL-NNN: Short action-oriented title

- Status: `not_started`
- Priority: `P2`
- Scope: `unscoped`
- Area: `subsystem/name`
- Current state or ambition: What exists and what is missing.
- Remaining work or required scoping:
  - Concrete item.
- Done when:
  - Verifiable completion condition.
- Dependencies: Task IDs or `None`.
- Sources: Relevant files, issues, reports, or decisions.
```
