"""Evaluation schema tests."""

from pydantic import ValidationError

from combatrl.core.constants import METRICS_SCHEMA_VERSION
from combatrl.schemas.evaluation import EvaluationResult, PolicySpec, ScenarioSpec


def test_valid_evaluation_result_passes() -> None:
    result = EvaluationResult(
        metrics_schema_version=METRICS_SCHEMA_VERSION,
        evaluation_id="eval_test",
        scenario_id="scenario",
        policy_id="aggressive",
        opponent_id="defensive",
        profile_id=None,
        num_matches=2,
        seed_start=10,
        aggregate_metrics={"win_rate": 0.5, "num_matches": 2.0},
        per_match_metrics_path="metrics.csv",
        replay_sample_paths=[],
    )

    assert result.num_matches == 2


def test_invalid_num_matches_fails() -> None:
    try:
        EvaluationResult(
            metrics_schema_version=METRICS_SCHEMA_VERSION,
            evaluation_id="eval_test",
            scenario_id="scenario",
            policy_id="aggressive",
            opponent_id="defensive",
            profile_id=None,
            num_matches=0,
            seed_start=10,
            aggregate_metrics={"win_rate": 0.5},
            per_match_metrics_path="metrics.csv",
            replay_sample_paths=[],
        )
    except ValidationError as exc:
        assert "num_matches" in str(exc)
    else:
        raise AssertionError("expected ValidationError")


def test_policy_spec_validates_variants() -> None:
    assert PolicySpec(policy_id="aggressive", policy_type="heuristic").policy_id == "aggressive"
    assert PolicySpec(policy_id="random", policy_type="random").policy_type == "random"
    assert (
        PolicySpec(
            policy_id="profiled:aggressive:defensive",
            policy_type="profiled",
            base_policy_id="aggressive",
            profile_id="defensive",
        ).profile_id
        == "defensive"
    )
    assert (
        PolicySpec(
            policy_id="model_final",
            policy_type="ppo_checkpoint",
            checkpoint_path="model_final.zip",
        ).checkpoint_path
        == "model_final.zip"
    )


def test_scenario_spec_requires_fields() -> None:
    scenario = ScenarioSpec(
        scenario_id="mvp_2v2",
        simulation_config_path="configs/env/mvp_2v2_elimination.yaml",
        env_config_path="configs/env/gym_2v2_controlled_ranged.yaml",
        controlled_agent_id="team0_ranged_dps_0",
        teammate_policy_id="protector",
        opponent_policy_ids=["aggressive", "random"],
    )

    assert scenario.controlled_agent_id == "team0_ranged_dps_0"
