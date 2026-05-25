from combatrl.schemas.actions import ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import load_simulation_config
from combatrl.schemas.match_state import MatchState
from combatrl.sim.engine import SimulationEngine


def make_engine(max_ticks: int = 200) -> SimulationEngine:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    config = config.model_copy(update={"max_ticks": max_ticks})
    return SimulationEngine(config=config, seed=42)


def make_state() -> MatchState:
    return make_engine().state


def eliminate(agent: AgentState) -> None:
    agent.hp = 0.0
    agent.alive = False


def movement_actions() -> set[ActionType]:
    return {
        ActionType.MOVE_UP,
        ActionType.MOVE_DOWN,
        ActionType.MOVE_LEFT,
        ActionType.MOVE_RIGHT,
        ActionType.MOVE_UP_LEFT,
        ActionType.MOVE_UP_RIGHT,
        ActionType.MOVE_DOWN_LEFT,
        ActionType.MOVE_DOWN_RIGHT,
    }
