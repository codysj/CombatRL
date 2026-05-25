"""Gymnasium-compatible single-agent environment wrapper."""

from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from numpy.typing import NDArray

from combatrl.agents.base import AgentPolicy
from combatrl.agents.registry import create_policy
from combatrl.core.constants import ACTION_SCHEMA_VERSION, OBSERVATION_SCHEMA_VERSION
from combatrl.envs.action_codec import ActionCodec
from combatrl.envs.observation_builder import OBS_DIM, ObservationBuilder, observation_to_numpy
from combatrl.envs.reward_builder import RewardBuilder
from combatrl.schemas.actions import ActionCommand
from combatrl.schemas.configs import (
    EnvironmentConfig,
    load_environment_config,
    load_simulation_config,
)
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog
from combatrl.sim.engine import SimulationEngine
from combatrl.sim.invariants import InvariantViolation


class CombatRLGymEnv(gym.Env[NDArray[np.float32], int]):
    """Thin Gymnasium wrapper around the deterministic CombatRL simulator."""

    metadata = {"render_modes": [None, "human", "rgb_array"], "render_fps": 30}

    def __init__(
        self,
        env_config: EnvironmentConfig | dict[str, Any] | str | Path,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()
        self.env_config = _coerce_env_config(env_config)
        if self.env_config.observation_schema_version != OBSERVATION_SCHEMA_VERSION:
            msg = f"observation_schema_version must be {OBSERVATION_SCHEMA_VERSION}"
            raise ValueError(msg)
        if self.env_config.action_schema_version != ACTION_SCHEMA_VERSION:
            msg = f"action_schema_version must be {ACTION_SCHEMA_VERSION}"
            raise ValueError(msg)
        self.simulation_config = load_simulation_config(self.env_config.simulation_config_path)
        self.render_mode = render_mode

        if self.env_config.controlled_agent_id not in {
            agent.agent_id for team in self.simulation_config.teams for agent in team.agents
        }:
            msg = f"controlled_agent_id {self.env_config.controlled_agent_id!r} is not in config"
            raise ValueError(msg)
        self._validate_scripted_policy_config()

        self.action_codec = ActionCodec()
        self.observation_builder = ObservationBuilder()
        self.reward_builder = RewardBuilder(self.env_config.reward_config)
        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )
        self.action_space = spaces.Discrete(self.action_codec.n_actions())

        self._engine: SimulationEngine | None = None
        self._policy_by_agent_id: dict[str, AgentPolicy] = {}
        self._seed = 0 if self.env_config.seed is None else self.env_config.seed
        self._done = False
        self._truncated_error: str | None = None

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[NDArray[np.float32], dict[str, Any]]:
        """Reset the simulator and return the initial observation and info."""
        super().reset(seed=seed)
        del options
        self._seed = self._seed if seed is None else seed
        self._engine = SimulationEngine(config=self.simulation_config, seed=self._seed)
        self._done = False
        self._truncated_error = None
        self._policy_by_agent_id = self._build_policy_map(self._engine.state, self._seed)
        observation = self._build_numpy_observation(self._engine.state)
        info = self._base_info(self._engine.state)
        info.update(
            {
                "reward_breakdown": None,
                "invalid_action": False,
                "action_mask": self.action_codec.valid_action_mask(
                    self._engine.state,
                    self.env_config.controlled_agent_id,
                ),
                "events_count": 0,
            }
        )
        return observation, info

    def step(
        self,
        action: int,
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict[str, Any]]:
        """Advance the environment by one RL decision step."""
        if self._engine is None:
            msg = "CombatRLGymEnv.step() called before reset()"
            raise RuntimeError(msg)
        if self._done:
            msg = "CombatRLGymEnv.step() called after termination/truncation; call reset()"
            raise RuntimeError(msg)

        previous_state = self._engine.state.model_copy(deep=True)
        action_id = int(action)
        action_mask = self.action_codec.valid_action_mask(
            previous_state,
            self.env_config.controlled_agent_id,
        )
        invalid_action = not (0 <= action_id < self.action_codec.n_actions())
        if not invalid_action and action_mask[action_id] == 0:
            invalid_action = True

        controlled_action = (
            self.action_codec.fallback_action(self.env_config.controlled_agent_id)
            if invalid_action
            else self.action_codec.decode(action_id, self.env_config.controlled_agent_id)
        )
        scripted_actions, action_metadata = self._scripted_actions(previous_state)
        step_events: list[EventLog] = []

        try:
            for _ in range(self.env_config.decision_interval_ticks):
                if self._engine.state.terminal:
                    break
                self._engine.step(
                    [controlled_action, *scripted_actions],
                    action_metadata={
                        self.env_config.controlled_agent_id: {"policy_id": "rl"},
                        **action_metadata,
                    },
                )
                step_events.extend(self._engine.last_events)
        except InvariantViolation as exc:
            self._truncated_error = str(exc)

        current_state = self._engine.state
        controlled_death_termination = (
            self.env_config.terminate_on_controlled_death
            and not current_state.agents[self.env_config.controlled_agent_id].alive
            and not current_state.terminal
        )

        reward_breakdown = self.reward_builder.compute(
            previous_state=previous_state,
            current_state=current_state,
            events=step_events,
            controlled_agent_id=self.env_config.controlled_agent_id,
            invalid_action=invalid_action,
        )
        observation = self._build_numpy_observation(current_state)

        terminated = (
            (current_state.terminal and current_state.terminal_reason == "elimination")
            or controlled_death_termination
        ) and self._truncated_error is None
        truncated = self._truncated_error is not None or (
            current_state.terminal and current_state.terminal_reason == "timeout"
        )
        self._done = terminated or truncated

        next_action_mask = self.action_codec.valid_action_mask(
            current_state,
            self.env_config.controlled_agent_id,
        )
        info = self._base_info(current_state)
        info.update(
            {
                "reward_breakdown": reward_breakdown.model_dump(mode="json"),
                "invalid_action": invalid_action,
                "terminal_reason": self._terminal_reason(
                    current_state,
                    truncated,
                    controlled_death_termination,
                ),
                "winner_team_id": current_state.winner_team_id,
                "action_mask": next_action_mask,
                "events_count": len(step_events),
            }
        )
        if self._truncated_error is not None:
            info["error"] = self._truncated_error
        return observation, float(reward_breakdown.total_reward), terminated, truncated, info

    def render(self) -> Any:
        """Render support is intentionally minimal for P5."""
        if self.render_mode is None or self.render_mode == "human":
            return None
        if self.render_mode == "rgb_array":
            msg = "rgb_array rendering is not implemented for the P5 Gymnasium wrapper"
            raise NotImplementedError(msg)
        msg = f"unsupported render_mode: {self.render_mode!r}"
        raise ValueError(msg)

    def close(self) -> None:
        """Release environment resources."""
        self._engine = None
        self._policy_by_agent_id = {}

    def _build_policy_map(self, state: MatchState, seed: int) -> dict[str, AgentPolicy]:
        controlled_agent = state.agents[self.env_config.controlled_agent_id]
        opponents = [
            agent_id
            for agent_id in sorted(state.agents)
            if state.agents[agent_id].team_id != controlled_agent.team_id
        ]
        teammates = [
            agent_id
            for agent_id in sorted(state.agents)
            if agent_id != controlled_agent.agent_id
            and state.agents[agent_id].team_id == controlled_agent.team_id
        ]

        policy_by_agent_id: dict[str, AgentPolicy] = {}
        if self.env_config.scripted_policy_by_agent_id is not None:
            scripted_policy_ids = self.env_config.scripted_policy_by_agent_id
            for index, agent_id in enumerate(sorted(opponents + teammates)):
                policy_id = scripted_policy_ids[agent_id]
                policy = create_policy(policy_id, seed=seed + 100 + index)
                policy.reset(seed + 100 + index)
                policy_by_agent_id[agent_id] = policy
            return policy_by_agent_id

        for index, agent_id in enumerate(teammates):
            policy_id = self.env_config.teammate_policy_id or "random"
            policy = create_policy(policy_id, seed=seed + 100 + index)
            policy.reset(seed + 100 + index)
            policy_by_agent_id[agent_id] = policy
        for index, agent_id in enumerate(opponents):
            policy_id = _policy_id_for_index(self.env_config.opponent_policy_ids, index)
            policy = create_policy(policy_id, seed=seed + 200 + index)
            policy.reset(seed + 200 + index)
            policy_by_agent_id[agent_id] = policy
        return policy_by_agent_id

    def _scripted_actions(
        self,
        state: MatchState,
    ) -> tuple[list[ActionCommand], dict[str, dict[str, object]]]:
        actions: list[ActionCommand] = []
        metadata: dict[str, dict[str, object]] = {}
        for agent_id in sorted(self._policy_by_agent_id):
            policy = self._policy_by_agent_id[agent_id]
            actions.append(policy.select_action(state, agent_id))
            metadata[agent_id] = {"policy_id": policy.policy_id}
        return actions, metadata

    def _build_numpy_observation(self, state: MatchState) -> NDArray[np.float32]:
        observation = self.observation_builder.build_observation(
            state,
            self.env_config.controlled_agent_id,
        )
        return observation_to_numpy(observation)

    def _base_info(self, state: MatchState) -> dict[str, Any]:
        controlled_agent = state.agents[self.env_config.controlled_agent_id]
        ally_agent_ids = [
            agent_id
            for agent_id in sorted(state.agents)
            if agent_id != controlled_agent.agent_id
            and state.agents[agent_id].team_id == controlled_agent.team_id
        ]
        enemy_agent_ids = [
            agent_id
            for agent_id in sorted(state.agents)
            if state.agents[agent_id].team_id != controlled_agent.team_id
        ]
        team0_agents = [agent for agent in state.agents.values() if agent.team_id == 0]
        team1_agents = [agent for agent in state.agents.values() if agent.team_id == 1]
        return {
            "match_id": state.match_id,
            "seed": state.seed,
            "controlled_agent_id": self.env_config.controlled_agent_id,
            "controlled_team_id": controlled_agent.team_id,
            "ally_agent_ids": ally_agent_ids,
            "enemy_agent_ids": enemy_agent_ids,
            "scenario_id": self.simulation_config.scenario_id,
            "tick": state.tick,
            "terminal_reason": state.terminal_reason,
            "winner_team_id": state.winner_team_id,
            "team0_alive": sum(1 for agent in team0_agents if agent.alive),
            "team1_alive": sum(1 for agent in team1_agents if agent.alive),
            "controlled_agent_alive": controlled_agent.alive,
            "ally_alive_count": sum(
                1 for agent_id in ally_agent_ids if state.agents[agent_id].alive
            ),
            "enemy_alive_count": sum(
                1 for agent_id in enemy_agent_ids if state.agents[agent_id].alive
            ),
        }

    def _validate_scripted_policy_config(self) -> None:
        agent_ids = {
            agent.agent_id for team in self.simulation_config.teams for agent in team.agents
        }
        controlled_agent_id = self.env_config.controlled_agent_id
        non_controlled_agent_ids = sorted(agent_ids - {controlled_agent_id})
        if self.env_config.scripted_policy_by_agent_id is not None:
            scripted_agent_ids = set(self.env_config.scripted_policy_by_agent_id)
            non_controlled_agent_id_set = set(non_controlled_agent_ids)
            extra_agent_ids = scripted_agent_ids - non_controlled_agent_id_set
            missing_agent_ids = non_controlled_agent_id_set - scripted_agent_ids
            if controlled_agent_id in scripted_agent_ids:
                msg = "scripted_policy_by_agent_id must not include the controlled agent"
                raise ValueError(msg)
            if extra_agent_ids:
                msg = (
                    "scripted_policy_by_agent_id contains unknown agents: "
                    f"{sorted(extra_agent_ids)}"
                )
                raise ValueError(msg)
            if missing_agent_ids:
                msg = (
                    "scripted_policy_by_agent_id must assign every non-controlled agent; "
                    f"missing: {sorted(missing_agent_ids)}"
                )
                raise ValueError(msg)
            for policy_id in self.env_config.scripted_policy_by_agent_id.values():
                _validate_policy_id(policy_id)
            return

        if self.env_config.teammate_policy_id is not None:
            _validate_policy_id(self.env_config.teammate_policy_id)
        for policy_id in self.env_config.opponent_policy_ids:
            _validate_policy_id(policy_id)

    def _terminal_reason(
        self,
        state: MatchState,
        truncated: bool,
        controlled_death_termination: bool,
    ) -> str | None:
        if self._truncated_error is not None:
            return "invariant_failure"
        if controlled_death_termination:
            return "controlled_agent_dead"
        if truncated and state.terminal_reason == "timeout":
            return "max_ticks"
        return state.terminal_reason


def _coerce_env_config(
    env_config: EnvironmentConfig | dict[str, Any] | str | Path,
) -> EnvironmentConfig:
    if isinstance(env_config, EnvironmentConfig):
        return env_config
    if isinstance(env_config, dict):
        return EnvironmentConfig.model_validate(env_config)

    config_path = Path(env_config)
    loaded = load_environment_config(config_path)
    simulation_path = Path(loaded.simulation_config_path)
    if not simulation_path.is_absolute() and not simulation_path.exists():
        candidate = config_path.parent / simulation_path
        if candidate.exists():
            loaded = loaded.model_copy(update={"simulation_config_path": candidate})
    return loaded


def _policy_id_for_index(policy_ids: list[str], index: int) -> str:
    if not policy_ids:
        return "random"
    if index < len(policy_ids):
        return policy_ids[index]
    return policy_ids[-1]


def _validate_policy_id(policy_id: str) -> None:
    create_policy(policy_id, seed=0)
