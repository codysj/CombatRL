"""Lightweight profile behavior metrics."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from combatrl.agents.utility import (
    direction_action_away,
    direction_action_toward,
    get_live_allies,
    get_lowest_hp_enemy,
    get_nearest_ally,
    get_nearest_enemy,
)
from combatrl.core.geometry import distance
from combatrl.replay.reader import ReplayReader
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog, ReplayFrame

METRIC_FIELDS: tuple[str, ...] = (
    "avg_damage_dealt",
    "avg_damage_taken",
    "avg_survival_ticks",
    "avg_distance_to_nearest_enemy",
    "avg_distance_to_ally",
    "attack_action_rate",
    "retreat_action_rate",
    "low_hp_chase_rate",
    "shared_target_rate",
    "ally_peel_rate",
    "profile_behavior_separation_score",
    "win_rate",
)


@dataclass
class ProfileMetricsAccumulator:
    """Collect coarse behavior metrics for one episode."""

    team_id: int = 0
    focus_agent_id: str | None = None
    damage_dealt: float = 0.0
    damage_taken: float = 0.0
    attack_actions: int = 0
    retreat_actions: int = 0
    low_hp_chases: int = 0
    shared_target_attacks: int = 0
    ally_peel_actions: int = 0
    live_action_count: int = 0
    distance_to_enemy_sum: float = 0.0
    distance_to_ally_sum: float = 0.0
    enemy_distance_samples: int = 0
    ally_distance_samples: int = 0
    survival_tick_by_agent_id: dict[str, int] = field(default_factory=dict)
    scoped_agent_ids: set[str] = field(default_factory=set)

    def observe_state(self, state: MatchState) -> None:
        """Sample distances and live survival ticks from a state."""
        for agent_id in self._scope_agent_ids(state):
            agent = state.agents[agent_id]
            if agent.alive:
                self.survival_tick_by_agent_id[agent_id] = state.tick
                nearest_enemy = get_nearest_enemy(state, agent_id)
                if nearest_enemy is not None:
                    self.distance_to_enemy_sum += distance(agent.position, nearest_enemy.position)
                    self.enemy_distance_samples += 1
                nearest_ally = get_nearest_ally(state, agent_id)
                if nearest_ally is not None:
                    self.distance_to_ally_sum += distance(agent.position, nearest_ally.position)
                    self.ally_distance_samples += 1

    def observe_actions(self, state: MatchState, actions: list[ActionCommand]) -> None:
        """Record selected action rates from a pre-step state."""
        scoped_ids = self._scope_agent_ids(state)
        for action in actions:
            agent = state.agents.get(action.agent_id)
            if agent is None or not agent.alive or action.agent_id not in scoped_ids:
                continue
            self.live_action_count += 1
            if action.action_type == ActionType.ATTACK_NEAREST:
                self.attack_actions += 1
                if _attacks_shared_target(state, agent):
                    self.shared_target_attacks += 1
            nearest_enemy = get_nearest_enemy(state, action.agent_id)
            if nearest_enemy is not None and action.action_type == direction_action_away(
                agent.position,
                nearest_enemy.position,
            ):
                self.retreat_actions += 1
            lowest_hp_enemy = get_lowest_hp_enemy(state, action.agent_id)
            if lowest_hp_enemy is not None and lowest_hp_enemy.hp / lowest_hp_enemy.max_hp < 0.35:
                chase_action = direction_action_toward(agent.position, lowest_hp_enemy.position)
                if action.action_type == chase_action:
                    self.low_hp_chases += 1
            if _is_ally_peel_action(state, agent, action):
                self.ally_peel_actions += 1

    def observe_events(self, state: MatchState, events: list[EventLog]) -> None:
        """Record damage from simulator events."""
        scoped_ids = self._scope_agent_ids(state)
        for event in events:
            if event.event_type != "agent_damaged":
                continue
            damage = float(event.payload.get("damage", 0.0))
            if event.source_agent_id in scoped_ids:
                self.damage_dealt += damage
            if event.target_agent_id in scoped_ids:
                self.damage_taken += damage

    def finalize(self, state: MatchState) -> dict[str, float]:
        """Return normalized metrics for one episode."""
        scoped_ids = self._scope_agent_ids(state)
        agent_count = max(1, len(scoped_ids))
        winner = 1.0 if state.winner_team_id == self.team_id else 0.0
        return {
            "avg_damage_dealt": self.damage_dealt / agent_count,
            "avg_damage_taken": self.damage_taken / agent_count,
            "avg_survival_ticks": sum(
                self.survival_tick_by_agent_id.get(agent_id, 0) for agent_id in scoped_ids
            )
            / agent_count,
            "avg_distance_to_nearest_enemy": _safe_mean(
                self.distance_to_enemy_sum,
                self.enemy_distance_samples,
            ),
            "avg_distance_to_ally": _safe_mean(
                self.distance_to_ally_sum, self.ally_distance_samples
            ),
            "attack_action_rate": _safe_mean(self.attack_actions, self.live_action_count),
            "retreat_action_rate": _safe_mean(self.retreat_actions, self.live_action_count),
            "low_hp_chase_rate": _safe_mean(self.low_hp_chases, self.live_action_count),
            "shared_target_rate": _safe_mean(self.shared_target_attacks, self.attack_actions),
            "ally_peel_rate": _safe_mean(self.ally_peel_actions, self.live_action_count),
            "profile_behavior_separation_score": 0.0,
            "win_rate": winner,
        }

    def _scope_agent_ids(self, state: MatchState) -> set[str]:
        if self.scoped_agent_ids:
            return self.scoped_agent_ids
        if self.focus_agent_id is not None:
            self.scoped_agent_ids = {self.focus_agent_id}
        else:
            self.scoped_agent_ids = {
                agent_id
                for agent_id, agent in state.agents.items()
                if agent.team_id == self.team_id
            }
        for agent_id in self.scoped_agent_ids:
            self.survival_tick_by_agent_id.setdefault(agent_id, 0)
        return self.scoped_agent_ids


def aggregate_metric_dicts(metric_dicts: list[dict[str, float]]) -> dict[str, float]:
    """Average a list of episode metric dictionaries."""
    if not metric_dicts:
        return {field_name: 0.0 for field_name in METRIC_FIELDS}
    aggregate: dict[str, float] = {}
    for field_name in METRIC_FIELDS:
        aggregate[field_name] = sum(metrics.get(field_name, 0.0) for metrics in metric_dicts) / len(
            metric_dicts
        )
    return aggregate


def profile_behavior_separation_score(
    metrics: dict[str, float],
    baseline_metrics: dict[str, float],
) -> float:
    """Return a coarse normalized absolute behavior delta from a baseline."""
    components = (
        abs(metrics["attack_action_rate"] - baseline_metrics["attack_action_rate"]),
        abs(metrics["retreat_action_rate"] - baseline_metrics["retreat_action_rate"]),
        abs(
            metrics["avg_distance_to_nearest_enemy"]
            - baseline_metrics["avg_distance_to_nearest_enemy"]
        )
        / 100.0,
        abs(metrics["avg_distance_to_ally"] - baseline_metrics["avg_distance_to_ally"]) / 100.0,
        abs(metrics["low_hp_chase_rate"] - baseline_metrics["low_hp_chase_rate"]),
        abs(metrics["ally_peel_rate"] - baseline_metrics["ally_peel_rate"]),
    )
    return sum(components) / len(components)


def compute_profile_metrics_from_replay(
    replay_path: str | Path,
    *,
    team_id: int = 0,
    focus_agent_id: str | None = None,
) -> dict[str, float]:
    """Compute profile metrics from a saved replay directory."""
    reader = ReplayReader(replay_path)
    metadata = reader.load_metadata()
    frames = reader.load_frames()
    events = reader.load_events()
    if not frames:
        return {field_name: 0.0 for field_name in METRIC_FIELDS}

    frame_by_tick = {frame.tick: frame for frame in frames}
    accumulator = ProfileMetricsAccumulator(team_id=team_id, focus_agent_id=focus_agent_id)
    for frame in frames:
        accumulator.observe_state(_state_from_frame(frame, metadata.config))

    for event in events:
        if event.event_type == "agent_action_selected" and event.source_agent_id is not None:
            previous_frame = frame_by_tick.get(max(0, event.tick - 1))
            if previous_frame is None:
                continue
            action_type = ActionType(str(event.payload.get("action_type", ActionType.NO_OP)))
            accumulator.observe_actions(
                _state_from_frame(previous_frame, metadata.config),
                [ActionCommand(agent_id=event.source_agent_id, action_type=action_type)],
            )
        elif event.event_type == "agent_damaged":
            frame = frame_by_tick.get(event.tick) or frames[-1]
            accumulator.observe_events(_state_from_frame(frame, metadata.config), [event])

    final_state = _state_from_frame(frames[-1], metadata.config)
    final_state.winner_team_id = reader.load_summary().winner_team_id
    return accumulator.finalize(final_state)


def _state_from_frame(frame: ReplayFrame, config: dict[str, Any]) -> MatchState:
    return MatchState(
        match_id=frame.match_id,
        seed=int(config.get("seed", 0)),
        tick=frame.tick,
        max_ticks=max(int(config.get("max_ticks", frame.tick)), frame.tick, 1),
        tick_rate_hz=int(config.get("tick_rate_hz", 20)),
        arena_width=float(config.get("arena_width", 100.0)),
        arena_height=float(config.get("arena_height", 60.0)),
        agents={agent.agent_id: agent.model_copy(deep=True) for agent in frame.agents},
        obstacles=[],
        terminal=frame.scoreboard.get("terminal_reason") is not None,
        winner_team_id=_as_optional_int(frame.scoreboard.get("winner_team_id")),
        terminal_reason=_as_optional_str(frame.scoreboard.get("terminal_reason")),
    )


def _attacks_shared_target(state: MatchState, agent: AgentState) -> bool:
    nearest_enemy = get_nearest_enemy(state, agent.agent_id)
    if nearest_enemy is None:
        return False
    return any(
        ally.current_target_id == nearest_enemy.agent_id
        for ally in get_live_allies(state, agent.agent_id)
    )


def _is_ally_peel_action(state: MatchState, agent: AgentState, action: ActionCommand) -> bool:
    allies = get_live_allies(state, agent.agent_id)
    if not allies:
        return False
    threatened_ally = min(
        allies,
        key=lambda ally: (
            ally.hp / ally.max_hp,
            _nearest_enemy_distance(state, ally),
            ally.agent_id,
        ),
    )
    threat = _nearest_enemy_to_agent(state, threatened_ally)
    if threat is None:
        return False
    threat_distance = distance(threat.position, threatened_ally.position)
    if threat_distance > max(threatened_ally.attack_range, 8.0):
        return False
    return action.action_type in {
        ActionType.ATTACK_NEAREST,
        direction_action_toward(agent.position, threat.position),
        direction_action_toward(agent.position, threatened_ally.position),
    }


def _nearest_enemy_to_agent(state: MatchState, agent: AgentState) -> AgentState | None:
    enemies = [
        candidate
        for candidate in state.agents.values()
        if candidate.alive and candidate.team_id != agent.team_id
    ]
    if not enemies:
        return None
    return min(
        enemies, key=lambda enemy: (distance(agent.position, enemy.position), enemy.agent_id)
    )


def _nearest_enemy_distance(state: MatchState, agent: AgentState) -> float:
    enemy = _nearest_enemy_to_agent(state, agent)
    if enemy is None:
        return float("inf")
    return distance(agent.position, enemy.position)


def _safe_mean(value: float, count: int) -> float:
    if count == 0:
        return 0.0
    return value / count


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
