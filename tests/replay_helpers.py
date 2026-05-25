from pathlib import Path

from combatrl.core.geometry import distance
from combatrl.replay.writer import ReplayWriter
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import make_event_log
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.snapshots import build_replay_frame, build_replay_summary


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
    if abs(dx) >= abs(dy):
        return ActionType.MOVE_RIGHT if dx > 0.0 else ActionType.MOVE_LEFT
    return ActionType.MOVE_DOWN if dy > 0.0 else ActionType.MOVE_UP


def scripted_actions(state: MatchState) -> list[ActionCommand]:
    actions: list[ActionCommand] = []
    for agent in sorted(state.agents.values(), key=lambda item: item.agent_id):
        target = nearest_alive_enemy(state, agent)
        if not agent.alive or target is None:
            action_type = ActionType.NO_OP
        elif distance(agent.position, target.position) <= agent.attack_range:
            action_type = ActionType.ATTACK_NEAREST
        else:
            action_type = movement_toward(agent, target)
        actions.append(ActionCommand(agent_id=agent.agent_id, action_type=action_type))
    return actions


def run_scripted_replay(output_root: Path, seed: int = 42) -> tuple[Path, SimulationEngine]:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=seed)
    writer = ReplayWriter(output_root=output_root, use_timestamp=False)
    replay_path = writer.start_match(config=config, state=engine.state, seed=seed)
    initial_events = [
        make_event_log(
            match_id=engine.state.match_id,
            tick=0,
            index=0,
            event_type="match_started",
            payload={"scenario_id": config.scenario_id, "seed": seed},
        )
    ]
    writer.write_events(initial_events)
    writer.write_frame(build_replay_frame(engine.state, initial_events))

    while not engine.state.terminal:
        engine.step(scripted_actions(engine.state))
        step_events = engine.last_events
        writer.write_events(step_events)
        writer.write_frame(build_replay_frame(engine.state, step_events))

    summary = build_replay_summary(
        config=config,
        state=engine.state,
        frame_count=writer.frame_count,
        event_count=writer.event_count,
    )
    writer.finish(summary)
    return replay_path, engine
