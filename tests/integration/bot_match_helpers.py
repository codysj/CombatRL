from pathlib import Path

from combatrl.agents.base import AgentPolicy
from combatrl.agents.registry import create_policy
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary


def build_team_policies(
    state: MatchState,
    team0_policy_id: str,
    team1_policy_id: str,
    seed: int,
) -> dict[str, AgentPolicy]:
    policies = {
        0: create_policy(team0_policy_id, seed=seed),
        1: create_policy(team1_policy_id, seed=seed + 1),
    }
    for team_id, policy in policies.items():
        policy.reset(seed + team_id)
    return {agent_id: policies[state.agents[agent_id].team_id] for agent_id in sorted(state.agents)}


def run_bot_match(
    *,
    team0_policy_id: str,
    team1_policy_id: str,
    seed: int = 42,
    max_ticks: int = 240,
    output_root: Path | None = None,
) -> tuple[SimulationEngine, Path | None]:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    config = config.model_copy(update={"max_ticks": max_ticks})
    engine = SimulationEngine(config=config, seed=seed)
    policies = build_team_policies(engine.state, team0_policy_id, team1_policy_id, seed)
    writer: ReplayWriter | None = None
    replay_path: Path | None = None
    if output_root is not None:
        writer = ReplayWriter(output_root=output_root, use_timestamp=False)
        replay_path = writer.start_match(config=config, state=engine.state, seed=seed)
        initial_events = [
            make_event_log(
                match_id=engine.state.match_id,
                tick=0,
                index=0,
                event_type="match_started",
                payload={
                    "scenario_id": config.scenario_id,
                    "seed": seed,
                    "team0_policy": team0_policy_id,
                    "team1_policy": team1_policy_id,
                },
            )
        ]
        writer.write_events(initial_events)
        writer.write_frame(build_replay_frame(engine.state, initial_events))

    while not engine.state.terminal:
        actions = []
        metadata = {}
        for agent_id in sorted(engine.state.agents):
            policy = policies[agent_id]
            actions.append(policy.select_action(engine.state, agent_id))
            metadata[agent_id] = {"policy_id": policy.policy_id}
        engine.step(actions, action_metadata=metadata)
        if writer is not None:
            events = engine.last_events
            writer.write_events(events)
            writer.write_frame(build_replay_frame(engine.state, events))

    if writer is not None:
        summary = build_replay_summary(
            config=config,
            state=engine.state,
            frame_count=writer.frame_count,
            event_count=writer.event_count,
        )
        writer.finish(summary)
    return engine, replay_path
