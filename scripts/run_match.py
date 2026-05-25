"""Run a headless CombatRL match and optionally save a replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from combatrl.core.geometry import distance
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary

DEFAULT_CONFIG_PATH = Path("configs/env/mvp_2v2_elimination.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a headless CombatRL match.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-debug-invariants", action="store_true")
    parser.add_argument("--summary-every", type=int, default=100)
    parser.add_argument("--save-replay", action="store_true")
    parser.add_argument("--replay-dir", type=Path, default=Path("artifacts/replays"))
    parser.add_argument("--frame-interval", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def nearest_alive_enemy(state: MatchState, agent: AgentState) -> AgentState | None:
    enemies = [
        candidate
        for candidate in state.agents.values()
        if candidate.alive and candidate.team_id != agent.team_id
    ]
    if not enemies:
        return None
    return min(
        enemies, key=lambda enemy: (distance(agent.position, enemy.position), enemy.agent_id)
    )


def movement_toward(agent: AgentState, target: AgentState) -> ActionType:
    dx = target.position[0] - agent.position[0]
    dy = target.position[1] - agent.position[1]
    horizontal = ActionType.MOVE_RIGHT if dx > 0.0 else ActionType.MOVE_LEFT if dx < 0.0 else None
    vertical = ActionType.MOVE_DOWN if dy > 0.0 else ActionType.MOVE_UP if dy < 0.0 else None

    if vertical == ActionType.MOVE_UP and horizontal == ActionType.MOVE_LEFT:
        return ActionType.MOVE_UP_LEFT
    if vertical == ActionType.MOVE_UP and horizontal == ActionType.MOVE_RIGHT:
        return ActionType.MOVE_UP_RIGHT
    if vertical == ActionType.MOVE_DOWN and horizontal == ActionType.MOVE_LEFT:
        return ActionType.MOVE_DOWN_LEFT
    if vertical == ActionType.MOVE_DOWN and horizontal == ActionType.MOVE_RIGHT:
        return ActionType.MOVE_DOWN_RIGHT
    if vertical is not None:
        return vertical
    if horizontal is not None:
        return horizontal
    return ActionType.NO_OP


def scripted_actions(state: MatchState) -> list[ActionCommand]:
    actions: list[ActionCommand] = []
    for agent in sorted(state.agents.values(), key=lambda item: item.agent_id):
        if not agent.alive:
            actions.append(ActionCommand(agent_id=agent.agent_id, action_type=ActionType.NO_OP))
            continue

        target = nearest_alive_enemy(state, agent)
        if target is None:
            action_type = ActionType.NO_OP
        elif distance(agent.position, target.position) <= agent.attack_range:
            action_type = ActionType.ATTACK_NEAREST
        else:
            action_type = movement_toward(agent, target)
        actions.append(ActionCommand(agent_id=agent.agent_id, action_type=action_type))
    return actions


def print_tick_summary(state: MatchState) -> None:
    hp_summary = ", ".join(
        f"{agent.agent_id}:hp={agent.hp:.1f},alive={str(agent.alive).lower()}"
        for agent in sorted(state.agents.values(), key=lambda item: item.agent_id)
    )
    print(f"tick {state.tick}: {hp_summary}")


def main() -> int:
    args = parse_args()
    try:
        config = load_simulation_config(args.config)
        if args.max_ticks is not None:
            config = config.model_copy(update={"max_ticks": args.max_ticks})
        engine = SimulationEngine(
            config=config,
            seed=args.seed,
            debug_invariants=not args.no_debug_invariants,
        )
        replay_writer: ReplayWriter | None = None
        replay_path: Path | None = None
        if args.save_replay:
            replay_writer = ReplayWriter(
                output_root=args.replay_dir,
                frame_interval=args.frame_interval,
            )
            replay_path = replay_writer.start_match(
                config=config, state=engine.state, seed=args.seed
            )
            initial_events = [
                make_event_log(
                    match_id=engine.state.match_id,
                    tick=0,
                    index=0,
                    event_type="match_started",
                    payload={
                        "scenario_id": config.scenario_id,
                        "seed": args.seed,
                        "agent_count": len(engine.state.agents),
                    },
                )
            ]
            replay_writer.write_events(initial_events)
            replay_writer.write_frame(build_replay_frame(engine.state, initial_events))

        while not engine.state.terminal:
            engine.step(scripted_actions(engine.state))
            if replay_writer is not None:
                step_events = engine.last_events
                replay_writer.write_events(step_events)
                if engine.state.terminal or engine.state.tick % replay_writer.frame_interval == 0:
                    replay_writer.write_frame(build_replay_frame(engine.state, step_events))
            if (
                not args.quiet
                and args.summary_every > 0
                and engine.state.tick % args.summary_every == 0
            ):
                print_tick_summary(engine.state)
        final_state = engine.state
        if replay_writer is not None:
            summary = build_replay_summary(
                config=config,
                state=final_state,
                frame_count=replay_writer.frame_count,
                event_count=replay_writer.event_count,
            )
            replay_path = replay_writer.finish(summary)
            validate_replay(replay_path)
    except Exception as exc:
        print(f"run_match failed: {exc}", file=sys.stderr)
        return 1

    print(f"match_id: {final_state.match_id}")
    print(f"scenario_id: {config.scenario_id}")
    print(f"seed: {final_state.seed}")
    print(f"final_tick: {final_state.tick}")
    print(f"max_ticks: {final_state.max_ticks}")
    print(f"terminal: {str(final_state.terminal).lower()}")
    print(f"terminal_reason: {final_state.terminal_reason}")
    print(f"winner_team_id: {final_state.winner_team_id}")
    print(f"agent_count: {len(final_state.agents)}")
    print(f"simulated_duration_seconds: {final_state.tick / final_state.tick_rate_hz:.2f}")
    if replay_path is not None:
        print(f"replay_path: {replay_path}")
        print(f"replay_frame_count: {summary.frame_count}")
        print(f"replay_event_count: {summary.event_count}")
        print("replay_validation: passed")
    print("agents:")
    for agent in sorted(final_state.agents.values(), key=lambda item: item.agent_id):
        print(
            f"  - {agent.agent_id}: team={agent.team_id}, role={agent.role}, "
            f"hp={agent.hp:.1f}, alive={str(agent.alive).lower()}"
        )

    survivors = [agent.agent_id for agent in final_state.agents.values() if agent.alive]
    print(f"surviving_agents: {sorted(survivors)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
