from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from combatrl.schemas.configs import SimulationConfig, load_simulation_config

CONFIG_PATH = Path("configs/env/mvp_2v2_elimination.yaml")


def test_default_yaml_loads_into_simulation_config() -> None:
    config = load_simulation_config(CONFIG_PATH)

    assert isinstance(config, SimulationConfig)


def test_default_config_has_expected_scenario() -> None:
    config = load_simulation_config(CONFIG_PATH)

    assert config.scenario_id == "mvp_2v2_elimination"


def test_default_config_has_two_teams_and_four_agents() -> None:
    config = load_simulation_config(CONFIG_PATH)

    assert len(config.teams) == 2
    assert sum(len(team.agents) for team in config.teams) == 4


def test_duplicate_agent_ids_fail_validation() -> None:
    raw_config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_config["teams"][1]["agents"][0]["agent_id"] = "team0_tank_0"

    with pytest.raises(ValidationError):
        SimulationConfig.model_validate(raw_config)


def test_out_of_bounds_spawn_fails_validation() -> None:
    raw_config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_config["teams"][0]["agents"][0]["spawn_position"] = [-1.0, 25.0]

    with pytest.raises(ValidationError):
        SimulationConfig.model_validate(raw_config)
