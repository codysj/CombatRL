# CombatRL 3D Replay Viewer

The browser viewer is a visualization-only layer for existing CombatRL replay
artifacts. It reads saved files and never runs or recomputes simulator,
training, reward, Gymnasium, or evaluation logic.

## Stack

- Vite
- React
- TypeScript
- Three.js
- Vitest
- Yarn Plug'n'Play through Corepack

## Install and run

From the repository root:

```powershell
cd frontend
corepack yarn install
corepack yarn dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

Production build and tests:

```powershell
cd frontend
corepack yarn typecheck
corepack yarn test
corepack yarn build
```

## Demo replay

The first pass automatically loads:

```text
frontend/public/demo-replays/close-2v2/
```

This is an unchanged copy of the existing replay at:

```text
artifacts/checkpoints/ppo_curriculum_s4_close2v2/
  run_20260610T220347Z/sample_replays/
  20260610T220800Z_mvp_2v2_close_elimination_seed-123/
```

The viewer expects the standard replay files:

- `metadata.json`
- `frames.jsonl`
- `events.jsonl`
- `summary.json`

`metadata.json` supplies arena dimensions and config data. `frames.jsonl`
supplies authoritative positions, HP, roles, ranges, targets, and alive state.
`events.jsonl` supplies attack, damage, elimination, and match events.
`summary.json` supplies the terminal result and aggregate counts.

## Viewer behavior

- Simulation `(x, y)` maps to Three.js `(x, 0, z)`, centered on the arena.
- Positions interpolate between saved frames for smooth playback.
- HP, alive state, targets, and all combat effects come from saved replay data.
- Tank, ranged DPS, and fallback support models use procedural primitives.
- Team colors, HP bars, labels, range rings, target lines, attack beams,
  damage markers, and death markers are visual overlays only.
- Angled, top-down, and free orbit camera modes are available.
- Playback supports play/pause, reset, scrubbing, and 0.5x/1x/2x/4x speeds.
- Missing optional ranges, targets, or events disable the corresponding overlay
  with a non-blocking note.

## First-pass limitations

- The UI loads one bundled demo replay; local directory selection and a replay
  catalog/backend are not implemented.
- Replay files receive lightweight structural parsing rather than full browser-side
  Pydantic-equivalent schema validation.
- Event effects are intentionally simple and short-lived.
- Follow-agent cameras, audio, mobile-specific controls, live simulation, and
  generated 3D assets are not included.
- The viewer does not replace or modify the existing Pygame replay renderer.
