from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def make_engine(max_ticks: int = 1200) -> SimulationEngine:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    config = config.model_copy(update={"max_ticks": max_ticks})
    engine = SimulationEngine(config=config, seed=42)
    for agent in engine.state.agents.values():
        agent.position = (10.0, 10.0)
    return engine


def test_elimination_sets_terminal() -> None:
    engine = make_engine()
    engine.state.agents["team0_tank_0"].attack_damage = 999.0
    engine.state.agents["team1_ranged_dps_0"].hp = 0.0
    engine.state.agents["team1_ranged_dps_0"].alive = False

    engine.step(
        [
            ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST),
        ]
    )

    assert engine.state.terminal is True
    assert engine.state.terminal_reason == "elimination"


def test_elimination_sets_correct_winner_team_id() -> None:
    engine = make_engine()
    engine.state.agents["team0_tank_0"].attack_damage = 999.0
    engine.state.agents["team1_ranged_dps_0"].hp = 0.0
    engine.state.agents["team1_ranged_dps_0"].alive = False

    engine.step(
        [
            ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST),
        ]
    )

    assert engine.state.winner_team_id == 0


def test_timeout_still_works() -> None:
    engine = make_engine(max_ticks=3)

    engine.run_until_terminal()

    assert engine.state.tick == 3
    assert engine.state.terminal_reason == "timeout"
    assert engine.state.winner_team_id is None


def test_elimination_overrides_timeout_if_simultaneous() -> None:
    engine = make_engine(max_ticks=1)
    engine.state.agents["team0_tank_0"].attack_damage = 999.0
    engine.state.agents["team1_ranged_dps_0"].hp = 0.0
    engine.state.agents["team1_ranged_dps_0"].alive = False

    engine.step(
        [
            ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST),
        ]
    )

    assert engine.state.tick == 1
    assert engine.state.terminal_reason == "elimination"
    assert engine.state.winner_team_id == 0
