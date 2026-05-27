"""evaluate_policy.py integration smoke test."""

import os
import subprocess
import sys
from pathlib import Path


def test_evaluate_policy_script_runs_tiny_heuristic_eval(tmp_path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src;."
    command = [
        sys.executable,
        "scripts/evaluate_policy.py",
        "--scenario",
        "configs/env/gym_2v2_controlled_ranged.yaml",
        "--policy-type",
        "heuristic",
        "--policy-id",
        "aggressive",
        "--seed-start",
        "11",
        "--num-seeds",
        "2",
        "--replay-sample-count",
        "1",
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
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    assert "aggregate_json_path:" in completed.stdout
    assert "per_match_csv_path:" in completed.stdout
    assert "markdown_report_path:" in completed.stdout
