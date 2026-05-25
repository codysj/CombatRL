import math

from combatrl.core.geometry import distance
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.invariants import validate_match_state


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


def move_toward(agent: AgentState, target: AgentState) -> ActionType:
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
            action_type = move_toward(agent, target)
        actions.append(ActionCommand(agent_id=agent.agent_id, action_type=action_type))
    return actions


def test_scripted_match_reaches_terminal_without_crashing() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)

    while not engine.state.terminal:
        engine.step(scripted_actions(engine.state))
    final_state = engine.state

    assert final_state.terminal is True


def test_same_scripted_action_sequence_produces_identical_final_state() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine_a = SimulationEngine(config=config, seed=42)
    engine_b = SimulationEngine(config=config, seed=42)

    while not engine_a.state.terminal:
        actions = scripted_actions(engine_a.state)
        engine_a.step(actions)
        engine_b.step(actions)

    assert engine_a.state.model_dump(mode="json") == engine_b.state.model_dump(mode="json")


def test_no_nan_values_during_long_rollout() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)

    for _ in range(300):
        engine.step(scripted_actions(engine.state))
        for agent in engine.state.agents.values():
            assert math.isfinite(agent.position[0])
            assert math.isfinite(agent.position[1])
            assert math.isfinite(agent.hp)
        validate_match_state(engine.state)
        if engine.state.terminal:
            break


def test_varied_action_rollout_stays_valid() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)
    action_cycle = [
        ActionType.NO_OP,
        ActionType.MOVE_UP,
        ActionType.MOVE_DOWN,
        ActionType.MOVE_LEFT,
        ActionType.MOVE_RIGHT,
        ActionType.MOVE_UP_RIGHT,
        ActionType.ATTACK_NEAREST,
    ]

    for _ in range(50):
        actions = [
            ActionCommand(
                agent_id=agent_id,
                action_type=action_cycle[(engine.state.tick + index) % len(action_cycle)],
            )
            for index, agent_id in enumerate(sorted(engine.state.agents))
        ]
        engine.step(actions)
        validate_match_state(engine.state)
