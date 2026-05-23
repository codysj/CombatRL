from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def test_engine_tick_progression_and_timeout() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)

    assert engine.state.tick == 0

    engine.step()
    assert engine.state.tick == 1

    for _ in range(9):
        engine.step()
    assert engine.state.tick == 10

    final_state = engine.run_until_terminal()
    assert final_state.tick == config.max_ticks
    assert final_state.terminal is True
    assert final_state.terminal_reason == "timeout"
    assert final_state.winner_team_id is None

    engine.step()
    assert engine.state.tick == config.max_ticks
