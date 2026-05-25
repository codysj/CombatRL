from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine


def make_engine() -> SimulationEngine:
    config = load_simulation_config("configs/env/mvp_2v2_elimination.yaml")
    engine = SimulationEngine(config=config, seed=42)
    engine.state.agents["team0_tank_0"].position = (10.0, 10.0)
    engine.state.agents["team1_tank_0"].position = (15.0, 10.0)
    engine.state.agents["team1_ranged_dps_0"].position = (90.0, 10.0)
    return engine


def test_attack_nearest_damages_enemy_in_range() -> None:
    engine = make_engine()
    target = engine.state.agents["team1_tank_0"]

    engine.step([ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST)])

    assert target.hp == 146.0
    assert engine.state.agents["team0_tank_0"].attack_cooldown_ticks == 16


def test_attack_outside_range_fails() -> None:
    engine = make_engine()
    engine.state.agents["team1_tank_0"].position = (90.0, 10.0)
    target = engine.state.agents["team1_tank_0"]

    engine.step([ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST)])

    assert target.hp == target.max_hp
    assert engine.state.agents["team0_tank_0"].attack_cooldown_ticks == 0


def test_cooldown_prevents_repeated_attack_and_decrements() -> None:
    engine = make_engine()
    target = engine.state.agents["team1_tank_0"]

    action = [ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST)]
    engine.step(action)
    engine.step(action)

    assert target.hp == 146.0
    assert engine.state.agents["team0_tank_0"].attack_cooldown_ticks == 15


def test_dead_agents_cannot_attack() -> None:
    engine = make_engine()
    attacker = engine.state.agents["team0_tank_0"]
    target = engine.state.agents["team1_tank_0"]
    attacker.hp = 0.0
    attacker.alive = False

    engine.step([ActionCommand(agent_id=attacker.agent_id, action_type=ActionType.ATTACK_NEAREST)])

    assert target.hp == target.max_hp


def test_hp_clamps_at_zero() -> None:
    engine = make_engine()
    attacker = engine.state.agents["team0_tank_0"]
    target = engine.state.agents["team1_tank_0"]
    attacker.attack_damage = 999.0

    engine.step([ActionCommand(agent_id=attacker.agent_id, action_type=ActionType.ATTACK_NEAREST)])

    assert target.hp == 0.0
    assert target.alive is False


def test_deterministic_nearest_target_tie_breaking() -> None:
    engine = make_engine()
    engine.state.agents["team0_tank_0"].attack_range = 20.0
    engine.state.agents["team1_ranged_dps_0"].position = (15.0, 10.0)

    engine.step([ActionCommand(agent_id="team0_tank_0", action_type=ActionType.ATTACK_NEAREST)])

    assert engine.state.agents["team1_ranged_dps_0"].hp == 76.0
    assert engine.state.agents["team1_tank_0"].hp == 160.0
