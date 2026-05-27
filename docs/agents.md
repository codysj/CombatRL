# CombatRL Agents

Phase P4 provides simple, interpretable baseline policies. They use only
`MatchState` and public `ActionCommand` values, and they do not mutate simulator
state directly.

## Interface

Policies implement:

```python
policy_id: str
reset(seed: int | None = None) -> None
select_action(state: MatchState, agent_id: str) -> ActionCommand
```

## Policy IDs

- `random`: chooses uniformly among no-op, movement directions, and
  `ATTACK_NEAREST` when at least one live enemy exists.
- `aggressive`: targets the lowest-HP live enemy, attacks when ready and in
  range, otherwise moves toward the target.
- `defensive`: retreats when HP is below 40 percent or an enemy is too close,
  regroups with allies when isolated, and otherwise holds or attacks from safe
  range.
- `kiter`: moves away when too close, moves toward when too far, attacks at good
  range, and otherwise strafes deterministically.
- `protector`: identifies a vulnerable ally, stays near that ally, and attacks
  enemies threatening the ally.
- `profiled:<profile>`: wraps the aggressive base policy with a manual behavior
  profile.
- `profiled:<base_policy>:<profile>`: wraps a selected baseline with a manual
  behavior profile, for example `profiled:kiter:protective`.

## Running Matches

```powershell
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy kiter --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy protector --team1-policy aggressive --seed 42 --save-replay
uv run python scripts/run_match.py --team0-policy profiled:aggressive --team1-policy aggressive --seed 42 --save-replay
```

Role overrides are optional:

```powershell
uv run python scripts/run_match.py --team0-policy aggressive --team1-policy defensive --team0-tank-policy protector --team0-ranged-policy kiter --seed 42
uv run python scripts/run_match.py --team0-policy aggressive --team0-profile protective --team1-policy aggressive --seed 42
```

Saved bot replays remain P3 replay files and validate with:

```powershell
uv run python scripts/validate_replay.py <replay_path>
```

Render them with:

```powershell
uv run python scripts/render_replay.py <replay_path>
```

## Known Limitations

- The action space is still `NO_OP`, movement directions, and
  `ATTACK_NEAREST`; bots cannot issue explicit target IDs.
- Profiled bots still use the MVP action space; no explicit target-ID actions
  are added in P8.
- No support/healer behavior, objective-control mode, NLP command parser,
  frontend/backend, or full evaluation dashboard is included in P8.
