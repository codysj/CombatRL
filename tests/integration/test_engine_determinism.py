from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def test_same_seed_produces_identical_states() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine_a = SimulationEngine(config=config, seed=42)
    engine_b = SimulationEngine(config=config, seed=42)

    assert engine_a.state.model_dump(mode="json") == engine_b.state.model_dump(mode="json")

    for _ in range(37):
        engine_a.step()
        engine_b.step()

    assert engine_a.state.model_dump(mode="json") == engine_b.state.model_dump(mode="json")

    final_a = engine_a.run_until_terminal()
    final_b = engine_b.run_until_terminal()

    assert final_a.model_dump(mode="json") == final_b.model_dump(mode="json")


def test_different_seeds_are_allowed_to_match_before_randomized_systems_exist() -> None:
    # P1 stores the seed and match ID, but does not randomize spawns or mechanics yet.
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    state_a = SimulationEngine(config=config, seed=1).state
    state_b = SimulationEngine(config=config, seed=2).state

    assert state_a.seed != state_b.seed
    assert state_a.match_id != state_b.match_id
