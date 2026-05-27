"""Run a headless CombatRL match and optionally save a replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from combatrl.agents.base import AgentPolicy
from combatrl.agents.behavior_summary import BehaviorSummary
from combatrl.agents.profiled_bot import ProfiledBot
from combatrl.agents.registry import create_policy
from combatrl.profiles.loader import load_profile_by_id
from combatrl.replay.validators import validate_replay
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.actions import ActionCommand
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
    parser.add_argument("--team0-policy", default="aggressive")
    parser.add_argument("--team1-policy", default="aggressive")
    parser.add_argument("--team0-profile", default=None)
    parser.add_argument("--team1-profile", default=None)
    parser.add_argument("--team0-tank-policy", default=None)
    parser.add_argument("--team0-ranged-policy", default=None)
    parser.add_argument("--team1-tank-policy", default=None)
    parser.add_argument("--team1-ranged-policy", default=None)
    parser.add_argument("--no-debug-invariants", action="store_true")
    parser.add_argument("--summary-every", type=int, default=100)
    parser.add_argument("--save-replay", action="store_true")
    parser.add_argument("--replay-dir", type=Path, default=Path("artifacts/replays"))
    parser.add_argument("--frame-interval", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=None)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def build_policy_map(args: argparse.Namespace, state: MatchState) -> dict[str, AgentPolicy]:
    """Build one policy assignment for each agent ID."""
    team_policy_ids = {0: args.team0_policy, 1: args.team1_policy}
    role_overrides = {
        (0, "tank"): args.team0_tank_policy,
        (0, "ranged_dps"): args.team0_ranged_policy,
        (1, "tank"): args.team1_tank_policy,
        (1, "ranged_dps"): args.team1_ranged_policy,
    }
    policy_by_agent_id: dict[str, AgentPolicy] = {}
    for agent_id in sorted(state.agents):
        agent = state.agents[agent_id]
        policy_id = (
            role_overrides.get((agent.team_id, agent.role)) or team_policy_ids[agent.team_id]
        )
        policy = create_policy(policy_id, seed=args.seed + agent.team_id)
        profile_id = args.team0_profile if agent.team_id == 0 else args.team1_profile
        if profile_id is not None and not isinstance(policy, ProfiledBot):
            policy = ProfiledBot(policy, load_profile_by_id(profile_id))
        policy_by_agent_id[agent_id] = policy
    return policy_by_agent_id


def reset_policies(policy_by_agent_id: dict[str, AgentPolicy], seed: int) -> None:
    """Reset unique policy objects deterministically."""
    seen_policy_objects: set[int] = set()
    for index, agent_id in enumerate(sorted(policy_by_agent_id)):
        policy = policy_by_agent_id[agent_id]
        policy_identity = id(policy)
        if policy_identity in seen_policy_objects:
            continue
        seen_policy_objects.add(policy_identity)
        policy.reset(seed + index)


def policy_actions(
    state: MatchState,
    policy_by_agent_id: dict[str, AgentPolicy],
) -> tuple[list[ActionCommand], dict[str, dict[str, object]]]:
    """Ask each assigned policy for one action in stable agent order."""
    actions: list[ActionCommand] = []
    metadata: dict[str, dict[str, object]] = {}
    for agent_id in sorted(state.agents):
        policy = policy_by_agent_id[agent_id]
        action = policy.select_action(state, agent_id)
        actions.append(action)
        metadata[agent_id] = {
            "policy_id": policy.policy_id,
            "profile_id": getattr(policy, "profile_id", None),
            "valid": True,
            "fallback_used": False,
        }
    return actions, metadata


def print_tick_summary(state: MatchState) -> None:
    hp_summary = ", ".join(
        f"{agent.agent_id}:hp={agent.hp:.1f},alive={str(agent.alive).lower()}"
        for agent in sorted(state.agents.values(), key=lambda item: item.agent_id)
    )
    print(f"tick {state.tick}: {hp_summary}")


def remaining_hp_by_team(state: MatchState) -> dict[int, float]:
    totals = {0: 0.0, 1: 0.0}
    for agent in state.agents.values():
        totals[agent.team_id] += agent.hp
    return totals


def team_policy_summary(
    policy_by_agent_id: dict[str, AgentPolicy], state: MatchState
) -> dict[int, str]:
    policies_by_team: dict[int, set[str]] = {0: set(), 1: set()}
    for agent_id, policy in policy_by_agent_id.items():
        policies_by_team[state.agents[agent_id].team_id].add(policy.policy_id)
    return {
        team_id: ",".join(sorted(policy_ids)) for team_id, policy_ids in policies_by_team.items()
    }


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
        policy_by_agent_id = build_policy_map(args, engine.state)
        reset_policies(policy_by_agent_id, args.seed)
        behavior_summary = BehaviorSummary()
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
                        "team0_policy": args.team0_policy,
                        "team1_policy": args.team1_policy,
                        "team0_profile": args.team0_profile,
                        "team1_profile": args.team1_profile,
                    },
                )
            ]
            replay_writer.write_events(initial_events)
            replay_writer.write_frame(build_replay_frame(engine.state, initial_events))

        while not engine.state.terminal:
            actions, action_metadata = policy_actions(engine.state, policy_by_agent_id)
            behavior_summary.observe_actions(engine.state, actions)
            behavior_summary.observe_state(engine.state)
            engine.step(actions, action_metadata=action_metadata)
            if replay_writer is not None:
                step_events = engine.last_events
                behavior_summary.observe_events(engine.state, step_events)
                replay_writer.write_events(step_events)
                if engine.state.terminal or engine.state.tick % replay_writer.frame_interval == 0:
                    replay_writer.write_frame(build_replay_frame(engine.state, step_events))
            else:
                behavior_summary.observe_events(engine.state, engine.last_events)
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
    policies_by_team = team_policy_summary(policy_by_agent_id, final_state)
    print(f"team0_policy: {policies_by_team[0]}")
    print(f"team1_policy: {policies_by_team[1]}")
    print(f"final_tick: {final_state.tick}")
    print(f"max_ticks: {final_state.max_ticks}")
    print(f"terminal: {str(final_state.terminal).lower()}")
    print(f"terminal_reason: {final_state.terminal_reason}")
    print(f"winner_team_id: {final_state.winner_team_id}")
    hp_by_team = remaining_hp_by_team(final_state)
    print(f"team0_remaining_hp: {hp_by_team[0]:.1f}")
    print(f"team1_remaining_hp: {hp_by_team[1]:.1f}")
    print(f"team0_attack_attempts: {behavior_summary.attack_attempt_count[0]}")
    print(f"team1_attack_attempts: {behavior_summary.attack_attempt_count[1]}")
    print(f"team0_damage_dealt: {behavior_summary.damage_dealt[0]:.1f}")
    print(f"team1_damage_dealt: {behavior_summary.damage_dealt[1]:.1f}")
    print(f"team0_retreat_actions: {behavior_summary.retreat_action_count[0]}")
    print(f"team1_retreat_actions: {behavior_summary.retreat_action_count[1]}")
    average_distances = behavior_summary.average_distance_to_nearest_enemy()
    print(f"team0_avg_nearest_enemy_distance: {average_distances[0]:.2f}")
    print(f"team1_avg_nearest_enemy_distance: {average_distances[1]:.2f}")
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
