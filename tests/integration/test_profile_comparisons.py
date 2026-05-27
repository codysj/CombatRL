from pathlib import Path

from scripts.compare_profiles import run_profile_episode


def write_profile_test_scenario(path: Path) -> Path:
    scenario = path / "profile_test_scenario.yaml"
    scenario.write_text(
        """
config_schema_version: "1.0"
scenario_id: profile_test_scenario
tick_rate_hz: 20
max_ticks: 40
arena_width: 100.0
arena_height: 60.0
win_condition: elimination
teams:
  - team_id: 0
    agents:
      - agent_id: team0_tank_0
        team_id: 0
        role: tank
        spawn_position: [40.0, 30.0]
      - agent_id: team0_ranged_dps_0
        team_id: 0
        role: ranged_dps
        spawn_position: [70.0, 30.0]
  - team_id: 1
    agents:
      - agent_id: team1_tank_0
        team_id: 1
        role: tank
        spawn_position: [42.0, 30.0]
      - agent_id: team1_ranged_dps_0
        team_id: 1
        role: ranged_dps
        spawn_position: [90.0, 30.0]
obstacles: []
""",
        encoding="utf-8",
    )
    return scenario


def test_aggressive_vs_defensive_profile_comparison_has_behavior_delta(tmp_path) -> None:
    scenario = write_profile_test_scenario(tmp_path)
    aggressive_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="aggressive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=123,
        controlled_agent_id="team0_ranged_dps_0",
        replay_output_root=None,
        max_ticks=40,
    )
    defensive_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="defensive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=123,
        controlled_agent_id="team0_ranged_dps_0",
        replay_output_root=None,
        max_ticks=40,
    )

    assert aggressive_metrics != defensive_metrics
    assert aggressive_metrics["attack_action_rate"] > defensive_metrics["attack_action_rate"]


def test_defensive_profile_has_higher_retreat_rate_than_aggressive(tmp_path) -> None:
    scenario = write_profile_test_scenario(tmp_path)
    aggressive_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="aggressive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=124,
        controlled_agent_id="team0_tank_0",
        replay_output_root=None,
        max_ticks=40,
    )
    defensive_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="defensive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=124,
        controlled_agent_id="team0_tank_0",
        replay_output_root=None,
        max_ticks=40,
    )

    assert defensive_metrics["retreat_action_rate"] > aggressive_metrics["retreat_action_rate"]


def test_protective_profile_reduces_average_ally_distance(tmp_path) -> None:
    scenario = write_profile_test_scenario(tmp_path)
    aggressive_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="aggressive",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=125,
        controlled_agent_id=None,
        replay_output_root=None,
        max_ticks=40,
    )
    protective_metrics, _ = run_profile_episode(
        scenario_path=scenario,
        profile_id="protective",
        base_policy_id="aggressive",
        opponent_policy_id="aggressive",
        seed=125,
        controlled_agent_id=None,
        replay_output_root=None,
        max_ticks=40,
    )

    assert protective_metrics["avg_distance_to_ally"] < aggressive_metrics["avg_distance_to_ally"]
