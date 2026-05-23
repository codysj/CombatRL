from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def test_engine_initializes_mvp_agents_from_config() -> None:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    state = SimulationEngine(config=config, seed=42).state

    expected_ids = {
        "team0_tank_0",
        "team0_ranged_dps_0",
        "team1_tank_0",
        "team1_ranged_dps_0",
    }
    assert set(state.agents) == expected_ids
    assert len(state.agents) == 4

    for team in config.teams:
        for agent_config in team.agents:
            agent = state.agents[agent_config.agent_id]
            assert agent.role == agent_config.role
            assert agent.team_id == agent_config.team_id
            assert 0.0 <= agent.position[0] <= state.arena_width
            assert 0.0 <= agent.position[1] <= state.arena_height

    assert state.agents["team0_tank_0"].max_hp == 160.0
    assert state.agents["team1_tank_0"].max_hp == 160.0
    assert state.agents["team0_ranged_dps_0"].max_hp == 90.0
    assert state.agents["team1_ranged_dps_0"].max_hp == 90.0
