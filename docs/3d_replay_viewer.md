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

## Open a local replay

Select **Open replay** and choose a directory containing exactly one CombatRL
replay. The browser reads the four files locally; they are not uploaded or sent
to a service. Chromium-based browsers provide the intended directory picker.

The loader checks required files, JSON/JSONL syntax, schema version `1.0`,
required metadata/frame/event/summary fields, increasing frame ticks, replay
identity, terminal tick, and frame/event counts. Errors name the affected file,
line, and field where possible. A failed import leaves the current replay open
so the user can correct the selection or return to the bundled demo.

The Python replay validator remains the authoritative full validation path:

```powershell
uv run python scripts/validate_replay.py <replay-directory>
```

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
- Follow mode tracks a selected agent while preserving the current camera offset.
- Playback supports play/pause, reset, scrubbing, and 0.5x/1x/2x/4x speeds.
- Missing optional ranges, targets, or events disable the corresponding overlay
  with a non-blocking note.

## Keyboard controls

| Key | Action |
|---|---|
| `Space` | Play or pause |
| `Home` | Reset to the beginning |
| `Left` / `Right` | Seek backward or forward one second |
| `0`, `1`, `2`, `4` | Set 0.5x, 1x, 2x, or 4x speed |
| `C` | Cycle angled, top-down, and free cameras |
| `F` | Toggle follow mode for the selected agent |
| `R` | Toggle attack ranges |
| `T` | Toggle target lines |

Keyboard shortcuts are ignored while a form control has focus. Buttons expose
pressed/disabled state, focus indicators are visible, and compact layouts use
larger touch targets and horizontally scrollable camera/speed controls.

## Bundle budget

The 3D scene is lazy-loaded so replay parsing and the application shell do not
depend on the Three.js download. The minified renderer chunk has an explicit
560 kB warning budget (approximately 138 kB gzip in the current build). This is
accepted for the local, single-purpose viewer; exceeding the budget must trigger
a new splitting or dependency review.

## Limitations

- The UI opens one replay directory at a time; ZIP import, recent-file history,
  and a replay catalog/backend are not implemented.
- Directory selection relies on the Chromium `webkitdirectory` capability;
  cross-browser import behavior needs dedicated compatibility testing.
- Browser validation is intentionally scoped to safe viewing and useful errors;
  it does not replace the authoritative Python/Pydantic validator.
- Event effects are intentionally simple and short-lived.
- Audio and richer effects are intentionally deferred because they do not yet
  improve tactical clarity enough to justify more assets and controls.
- Live simulation and generated 3D assets are not included.
- The viewer does not replace or modify the existing Pygame replay renderer.
