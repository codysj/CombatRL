"""Benchmark suite integration tests."""

from pathlib import Path

from combatrl.evaluation.benchmark_suite import BenchmarkSuite
from combatrl.replay.validators import validate_replay
from combatrl.schemas.evaluation import PolicySpec, ScenarioSpec


def test_tiny_heuristic_benchmark_writes_outputs_and_is_deterministic(tmp_path) -> None:
    scenario = ScenarioSpec(
        scenario_id="mvp_2v2_elimination",
        simulation_config_path="configs/env/mvp_2v2_elimination.yaml",
        env_config_path="configs/env/gym_2v2_controlled_ranged.yaml",
        controlled_agent_id="team0_ranged_dps_0",
        teammate_policy_id="protector",
        opponent_policy_ids=["aggressive", "random"],
    )
    policy = PolicySpec(policy_id="aggressive", policy_type="heuristic")

    result_a = BenchmarkSuite(tmp_path / "a").run(
        scenario,
        policy,
        seeds=[7, 8],
        save_replays=True,
        replay_sample_count=1,
    )
    result_b = BenchmarkSuite(tmp_path / "b").run(
        scenario,
        policy,
        seeds=[7, 8],
        save_replays=True,
        replay_sample_count=1,
    )

    assert result_a.num_matches == 2
    assert Path(result_a.per_match_metrics_path).exists()
    assert (Path(result_a.per_match_metrics_path).parent / "evaluation_result.json").exists()
    assert result_a.replay_sample_paths
    validate_replay(result_a.replay_sample_paths[0])
    assert result_a.aggregate_metrics == result_b.aggregate_metrics
