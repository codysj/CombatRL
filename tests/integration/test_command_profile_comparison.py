import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from combatrl.evaluation.benchmark_suite import BenchmarkSuite
from combatrl.nlp.parser import parse_command_to_profile
from combatrl.nlp.validation import balanced_profile
from combatrl.profiles.loader import load_profile
from combatrl.replay.validators import validate_replay
from combatrl.schemas.evaluation import PolicySpec, ScenarioSpec


def test_parsed_aggressive_profile_changes_evaluation_metrics(tmp_path) -> None:
    base = balanced_profile()
    parsed = parse_command_to_profile("play aggressively", base_profile=base)
    assert parsed.success
    assert parsed.profile is not None

    balanced_path = _write_profile(tmp_path / "balanced.yaml", base)
    parsed_path = _write_profile(tmp_path / "parsed_aggressive.yaml", parsed.profile)
    scenario = _scenario()
    suite = BenchmarkSuite(tmp_path / "evaluations")
    balanced_result = suite.run(
        scenario,
        PolicySpec(
            policy_id="profiled:aggressive:balanced",
            policy_type="profiled",
            base_policy_id="aggressive",
            profile_id=base.profile_id,
            profile_path=str(balanced_path),
        ),
        seeds=[211, 212],
        save_replays=False,
        replay_sample_count=0,
    )
    parsed_result = suite.run(
        scenario,
        PolicySpec(
            policy_id=f"profiled:aggressive:{parsed.profile.profile_id}",
            policy_type="profiled",
            base_policy_id="aggressive",
            profile_id=parsed.profile.profile_id,
            profile_path=str(parsed_path),
        ),
        seeds=[211, 212],
        save_replays=False,
        replay_sample_count=0,
    )

    assert (
        parsed_result.aggregate_metrics["mean_attack_action_rate"]
        >= balanced_result.aggregate_metrics["mean_attack_action_rate"]
    )


def test_protect_ally_parses_and_profile_comparison_does_not_crash(tmp_path) -> None:
    parsed = parse_command_to_profile("protect ally", base_profile=balanced_profile())

    assert parsed.success
    assert parsed.profile is not None
    assert parsed.profile.protectiveness > balanced_profile().protectiveness
    assert parsed.profile.cohesion > balanced_profile().cohesion

    profile_path = _write_profile(tmp_path / "protect.yaml", parsed.profile)
    result = BenchmarkSuite(tmp_path / "protect_eval").run(
        _scenario(),
        PolicySpec(
            policy_id=f"profiled:aggressive:{parsed.profile.profile_id}",
            policy_type="profiled",
            base_policy_id="aggressive",
            profile_id=parsed.profile.profile_id,
            profile_path=str(profile_path),
        ),
        seeds=[220],
        save_replays=False,
        replay_sample_count=0,
    )

    assert result.num_matches == 1


def test_saved_parsed_profile_loads_through_existing_loader(tmp_path) -> None:
    parsed = parse_command_to_profile("kite backward", base_profile=balanced_profile())
    assert parsed.profile is not None
    profile_path = _write_profile(tmp_path / "kiter.yaml", parsed.profile)

    loaded = load_profile(profile_path)

    assert loaded == parsed.profile


def test_command_comparison_script_writes_reports_and_replay(tmp_path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src;."
    command = [
        sys.executable,
        "scripts/compare_command_profiles.py",
        "--commands",
        "play aggressively",
        "protect ally",
        "--num-seeds",
        "1",
        "--seed-start",
        "300",
        "--save-replays",
        "--output-dir",
        str(tmp_path),
    ]

    completed = subprocess.run(
        command,
        cwd=Path(__file__).parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )

    assert completed.returncode == 0, completed.stderr
    summary_path = _path_from_stdout(completed.stdout, "summary_json_path:")
    markdown_path = _path_from_stdout(completed.stdout, "comparison_markdown_path:")
    replay_path = _path_from_stdout(completed.stdout, "sample_replay_path[play aggressively]:")
    payload = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary_path.exists()
    assert markdown_path.exists()
    assert payload["rows"]
    validate_replay(replay_path)


def _scenario() -> ScenarioSpec:
    return ScenarioSpec(
        scenario_id="mvp_2v2_elimination",
        simulation_config_path="configs/env/mvp_2v2_elimination.yaml",
        env_config_path="configs/env/gym_2v2_controlled_ranged.yaml",
        controlled_agent_id="team0_ranged_dps_0",
        teammate_policy_id="protector",
        opponent_policy_ids=["aggressive", "random"],
    )


def _write_profile(path: Path, profile) -> Path:
    path.write_text(
        yaml.safe_dump(profile.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return path


def _path_from_stdout(stdout: str, prefix: str) -> Path:
    for line in stdout.splitlines():
        if line.startswith(prefix):
            return Path(line.split(":", 1)[1].strip())
    raise AssertionError(f"missing {prefix} in stdout:\n{stdout}")
