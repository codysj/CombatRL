"""Replay/event-based evaluation metrics.

Metrics are computed from saved frames and events. Metrics that require optional
intent evidence return ``None`` when that evidence is absent instead of
reconstructing simulator behavior.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from combatrl.core.geometry import distance
from combatrl.replay.reader import ReplayReader
from combatrl.schemas.actions import ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.replay import EventLog, ReplayFrame

MetricValue = float | int | str | None

RETREAT_ACTIONS = {
    ActionType.MOVE_UP,
    ActionType.MOVE_DOWN,
    ActionType.MOVE_LEFT,
    ActionType.MOVE_RIGHT,
    ActionType.MOVE_UP_LEFT,
    ActionType.MOVE_UP_RIGHT,
    ActionType.MOVE_DOWN_LEFT,
    ActionType.MOVE_DOWN_RIGHT,
}


def compute_match_metrics_from_replay(
    replay_path: str | Path,
    controlled_agent_id: str,
) -> dict[str, MetricValue]:
    """Load one replay directory and compute stable per-match metrics."""
    reader = ReplayReader(replay_path)
    frames = reader.load_frames()
    events = reader.load_events()
    metrics = compute_match_metrics_from_frames_events(frames, events, controlled_agent_id)
    try:
        summary = reader.load_summary()
    except FileNotFoundError:
        return metrics
    controlled_team_id = _controlled_team_id(frames, controlled_agent_id)
    metrics["terminal_reason"] = summary.terminal_reason
    metrics["winner_team_id"] = summary.winner_team_id
    metrics.update(
        _outcome_metrics(summary.winner_team_id, controlled_team_id, summary.terminal_reason)
    )
    return metrics


def compute_match_metrics_from_frames_events(
    frames: list[ReplayFrame] | list[Any],
    events: list[EventLog] | list[Any],
    controlled_agent_id: str,
) -> dict[str, MetricValue]:
    """Compute one-match metrics from replay frame and event objects."""
    if not frames:
        return _empty_metrics()

    sorted_frames = sorted(frames, key=lambda frame: int(frame.tick))
    sorted_events = sorted(events, key=lambda event: (int(event.tick), str(event.event_id)))
    first_frame = sorted_frames[0]
    final_frame = sorted_frames[-1]
    controlled_team_id = _controlled_team_id(sorted_frames, controlled_agent_id)
    final_agent = _agent_by_id(final_frame).get(controlled_agent_id)
    final_hp = 0.0 if final_agent is None else float(final_agent.hp)
    final_hp_norm = 0.0 if final_agent is None else _safe_div(final_agent.hp, final_agent.max_hp)
    terminal_reason = _scoreboard_value(final_frame, "terminal_reason")
    winner_team_id = _optional_int(_scoreboard_value(final_frame, "winner_team_id"))

    damage_dealt = 0.0
    damage_taken = 0.0
    eliminations = 0
    deaths = 0
    attack_attempts = 0
    successful_attacks = 0
    attack_actions = 0
    retreat_actions = 0
    no_op_actions = 0
    invalid_actions = 0
    low_hp_chases = 0
    shared_target_attacks = 0
    ally_peel_actions = 0
    target_intent_attack_actions = 0
    live_action_count = 0
    action_type_counts: dict[ActionType, int] = {at: 0 for at in ActionType}

    frame_by_tick = {int(frame.tick): frame for frame in sorted_frames}
    action_events_by_tick = _action_events_by_tick(sorted_events)
    for event in sorted_events:
        event_type = str(event.event_type)
        source_agent_id = event.source_agent_id
        target_agent_id = event.target_agent_id
        payload = event.payload if isinstance(event.payload, dict) else {}

        if event_type == "agent_damaged":
            damage = _float_payload(payload, "damage")
            if source_agent_id == controlled_agent_id:
                damage_dealt += damage
            if target_agent_id == controlled_agent_id:
                damage_taken += damage
        elif event_type == "agent_eliminated":
            if source_agent_id == controlled_agent_id:
                eliminations += 1
            if target_agent_id == controlled_agent_id:
                deaths += 1
        elif event_type == "agent_attacked" and source_agent_id == controlled_agent_id:
            successful_attacks += 1
        elif event_type == "agent_action_selected" and source_agent_id == controlled_agent_id:
            action_type = _action_type_from_payload(payload)
            previous_frame = _nearest_previous_frame(frame_by_tick, int(event.tick))
            previous_agent = (
                None
                if previous_frame is None
                else _agent_by_id(previous_frame).get(controlled_agent_id)
            )
            is_live_action = previous_agent is not None and previous_agent.alive
            if is_live_action:
                live_action_count += 1
                action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
            if payload.get("valid") is False or payload.get("fallback_used") is True:
                invalid_actions += 1
            if not is_live_action:
                continue
            if action_type == ActionType.ATTACK_NEAREST:
                attack_attempts += 1
                attack_actions += 1
                if "target_intent_id" in payload:
                    target_intent_attack_actions += 1
                    target_intent_id = _optional_str(payload.get("target_intent_id"))
                    if target_intent_id is not None and _has_shared_target_intent(
                        action_events_by_tick.get(int(event.tick), []),
                        controlled_agent_id,
                        controlled_team_id,
                        target_intent_id,
                        previous_frame,
                    ):
                        shared_target_attacks += 1
                    if (
                        target_intent_id is not None
                        and previous_frame is not None
                        and _is_ally_peel_target(
                            previous_frame, controlled_agent_id, target_intent_id
                        )
                    ):
                        ally_peel_actions += 1
            elif action_type == ActionType.NO_OP:
                no_op_actions += 1
            elif action_type in RETREAT_ACTIONS and previous_frame is not None:
                if _is_retreat_action(previous_frame, controlled_agent_id, action_type):
                    retreat_actions += 1
                if _is_low_hp_chase(previous_frame, controlled_agent_id, action_type):
                    low_hp_chases += 1

    frame_metrics = _compute_frame_metrics(sorted_frames, controlled_agent_id)
    survival_ticks = frame_metrics["survival_ticks"]
    action_rates: dict[str, MetricValue] = {
        f"action_rate_{at.value.lower()}": _safe_div(
            action_type_counts.get(at, 0), live_action_count
        )
        for at in ActionType
    }
    metrics: dict[str, MetricValue] = {
        **_outcome_metrics(winner_team_id, controlled_team_id, _optional_str(terminal_reason)),
        "damage_dealt": damage_dealt,
        "damage_taken": damage_taken,
        "eliminations": eliminations,
        "deaths": deaths,
        "attack_attempts": attack_attempts,
        "successful_attacks": successful_attacks,
        "damage_per_survival_tick": _safe_div(damage_dealt, max(float(survival_ticks), 1.0)),
        "survival_ticks": survival_ticks,
        "controlled_agent_died": 1 if final_agent is None or not final_agent.alive else 0,
        "final_hp": final_hp,
        "final_hp_norm": final_hp_norm,
        "avg_distance_to_nearest_enemy": frame_metrics["avg_distance_to_nearest_enemy"],
        "avg_distance_to_ally": frame_metrics["avg_distance_to_ally"],
        "time_in_attack_range_rate": frame_metrics["time_in_attack_range_rate"],
        "time_in_enemy_threat_range_rate": frame_metrics["time_in_enemy_threat_range_rate"],
        "center_control_rate": frame_metrics["center_control_rate"],
        "shared_target_rate": _optional_rate(
            shared_target_attacks, target_intent_attack_actions
        ),
        "ally_peel_rate": _optional_rate(
            ally_peel_actions, target_intent_attack_actions
        ),
        "teamwork_intent_evidence_rate": _safe_div(
            target_intent_attack_actions, attack_actions
        ),
        "ally_survival_ticks": frame_metrics["ally_survival_ticks"],
        "cohesion_score": frame_metrics["cohesion_score"],
        "attack_action_rate": _safe_div(attack_actions, live_action_count),
        "retreat_action_rate": _safe_div(retreat_actions, live_action_count),
        "low_hp_chase_rate": _safe_div(low_hp_chases, live_action_count),
        "no_op_rate": _safe_div(no_op_actions, live_action_count),
        "invalid_action_rate": _safe_div(
            invalid_actions,
            max(len(_controlled_action_events(sorted_events, controlled_agent_id)), 1),
        ),
        "terminal_reason": _optional_str(terminal_reason),
        "winner_team_id": winner_team_id,
        "controlled_team_id": controlled_team_id,
        "frame_count": len(sorted_frames),
        "event_count": len(sorted_events),
        "first_tick": int(first_frame.tick),
        "final_tick": int(final_frame.tick),
        "edge_occupancy_rate": frame_metrics["edge_occupancy_rate"],
        **action_rates,
    }
    return metrics


def _compute_frame_metrics(
    frames: list[ReplayFrame],
    controlled_agent_id: str,
) -> dict[str, float | int]:
    controlled_team_id = _controlled_team_id(frames, controlled_agent_id)
    enemy_distance_sum = 0.0
    ally_distance_sum = 0.0
    enemy_distance_samples = 0
    ally_distance_samples = 0
    attack_range_samples = 0
    enemy_threat_samples = 0
    center_samples = 0
    edge_samples = 0
    live_samples = 0
    survival_tick = int(frames[0].tick)
    ally_survival_by_id: dict[str, int] = {}

    # Determine arena bounds from scoreboard with fallback.
    arena_width_sb = frames[-1].scoreboard.get("arena_width", 100.0)
    arena_width_bounds = float(arena_width_sb) if isinstance(arena_width_sb, int | float) else 100.0
    arena_height_sb = frames[-1].scoreboard.get("arena_height", 60.0)
    arena_height_bounds = (
        float(arena_height_sb) if isinstance(arena_height_sb, int | float) else 60.0
    )

    for frame in frames:
        agents = _agent_by_id(frame)
        controlled = agents.get(controlled_agent_id)
        allies = [
            agent
            for agent in agents.values()
            if agent.agent_id != controlled_agent_id and agent.team_id == controlled_team_id
        ]
        for ally in allies:
            ally_survival_by_id.setdefault(ally.agent_id, 0)
            if ally.alive:
                ally_survival_by_id[ally.agent_id] = int(frame.tick)

        if controlled is None or not controlled.alive:
            continue
        live_samples += 1
        survival_tick = int(frame.tick)
        enemies = [
            agent
            for agent in agents.values()
            if agent.team_id != controlled.team_id and agent.alive
        ]
        live_allies = [agent for agent in allies if agent.alive]
        nearest_enemy = _nearest_agent(controlled, enemies)
        nearest_ally = _nearest_agent(controlled, live_allies)
        if nearest_enemy is not None:
            enemy_distance = distance(controlled.position, nearest_enemy.position)
            enemy_distance_sum += enemy_distance
            enemy_distance_samples += 1
            if enemy_distance <= controlled.attack_range:
                attack_range_samples += 1
            if enemy_distance <= nearest_enemy.attack_range:
                enemy_threat_samples += 1
        if nearest_ally is not None:
            ally_distance_sum += distance(controlled.position, nearest_ally.position)
            ally_distance_samples += 1
        if _in_center(frame, controlled):
            center_samples += 1
        wall_dist = min(
            controlled.position[0],
            arena_width_bounds - controlled.position[0],
            controlled.position[1],
            arena_height_bounds - controlled.position[1],
        )
        if wall_dist <= 5.0:
            edge_samples += 1

    avg_ally_distance = _safe_div(ally_distance_sum, ally_distance_samples)
    arena_width_value = frames[-1].scoreboard.get("arena_width", 100.0)
    arena_width = arena_width_value if isinstance(arena_width_value, int | float) else 100.0
    arena_diag = math.hypot(float(arena_width), 60.0)
    if frames:
        max_x = max(
            (agent.position[0] for frame in frames for agent in frame.agents), default=100.0
        )
        max_y = max((agent.position[1] for frame in frames for agent in frame.agents), default=60.0)
        arena_diag = max(math.hypot(max_x, max_y), 1.0)
    return {
        "survival_ticks": survival_tick,
        "avg_distance_to_nearest_enemy": _safe_div(enemy_distance_sum, enemy_distance_samples),
        "avg_distance_to_ally": avg_ally_distance,
        "time_in_attack_range_rate": _safe_div(attack_range_samples, live_samples),
        "time_in_enemy_threat_range_rate": _safe_div(enemy_threat_samples, live_samples),
        "center_control_rate": _safe_div(center_samples, live_samples),
        "edge_occupancy_rate": _safe_div(edge_samples, live_samples),
        "ally_survival_ticks": sum(ally_survival_by_id.values()),
        "cohesion_score": max(0.0, 1.0 - _safe_div(avg_ally_distance, arena_diag)),
    }


def _outcome_metrics(
    winner_team_id: int | None,
    controlled_team_id: int,
    terminal_reason: str | None,
) -> dict[str, int]:
    win = int(winner_team_id == controlled_team_id)
    draw = int(winner_team_id is None or terminal_reason in {"timeout", "max_ticks"})
    loss = int(not win and not draw)
    return {"win": win, "loss": loss, "draw_or_timeout": draw}


def _empty_metrics() -> dict[str, MetricValue]:
    action_rate_names = tuple(f"action_rate_{at.value.lower()}" for at in ActionType)
    names = (
        "win",
        "loss",
        "draw_or_timeout",
        "damage_dealt",
        "damage_taken",
        "eliminations",
        "deaths",
        "attack_attempts",
        "successful_attacks",
        "damage_per_survival_tick",
        "survival_ticks",
        "controlled_agent_died",
        "final_hp",
        "final_hp_norm",
        "avg_distance_to_nearest_enemy",
        "avg_distance_to_ally",
        "time_in_attack_range_rate",
        "time_in_enemy_threat_range_rate",
        "center_control_rate",
        "edge_occupancy_rate",
        "shared_target_rate",
        "ally_peel_rate",
        "ally_survival_ticks",
        "cohesion_score",
        "attack_action_rate",
        "retreat_action_rate",
        "low_hp_chase_rate",
        "no_op_rate",
        "invalid_action_rate",
        "frame_count",
        "event_count",
        "first_tick",
        "final_tick",
        *action_rate_names,
    )
    metrics: dict[str, MetricValue] = {name: 0.0 for name in names}
    metrics["shared_target_rate"] = None
    metrics["ally_peel_rate"] = None
    metrics["teamwork_intent_evidence_rate"] = 0.0
    return metrics


def _agent_by_id(frame: ReplayFrame) -> dict[str, AgentState]:
    return {agent.agent_id: agent for agent in frame.agents}


def _controlled_team_id(frames: list[ReplayFrame] | list[Any], controlled_agent_id: str) -> int:
    for frame in frames:
        agent = _agent_by_id(frame).get(controlled_agent_id)
        if agent is not None:
            return int(agent.team_id)
    return 0


def _nearest_agent(agent: AgentState, candidates: list[AgentState]) -> AgentState | None:
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda candidate: (distance(agent.position, candidate.position), candidate.agent_id),
    )


def _in_center(frame: ReplayFrame, agent: AgentState) -> bool:
    xs = [candidate.position[0] for candidate in frame.agents]
    ys = [candidate.position[1] for candidate in frame.agents]
    arena_width = max(max(xs, default=100.0), 1.0)
    arena_height = max(max(ys, default=60.0), 1.0)
    return (
        0.25 * arena_width <= agent.position[0] <= 0.75 * arena_width
        and 0.25 * arena_height <= agent.position[1] <= 0.75 * arena_height
    )


def _action_type_from_payload(payload: dict[str, Any]) -> ActionType:
    raw_value = payload.get("action_type", ActionType.NO_OP)
    try:
        return ActionType(str(raw_value))
    except ValueError:
        return ActionType.NO_OP


def _nearest_previous_frame(
    frame_by_tick: dict[int, ReplayFrame], event_tick: int
) -> ReplayFrame | None:
    for tick in range(event_tick - 1, -1, -1):
        frame = frame_by_tick.get(tick)
        if frame is not None:
            return frame
    return frame_by_tick.get(event_tick)


def _is_retreat_action(
    frame: ReplayFrame,
    controlled_agent_id: str,
    action_type: ActionType,
) -> bool:
    agents = _agent_by_id(frame)
    controlled = agents.get(controlled_agent_id)
    if controlled is None:
        return False
    enemies = [
        agent for agent in agents.values() if agent.alive and agent.team_id != controlled.team_id
    ]
    nearest_enemy = _nearest_agent(controlled, enemies)
    if nearest_enemy is None:
        return False
    action_vector = _action_vector(action_type)
    enemy_vector = (
        nearest_enemy.position[0] - controlled.position[0],
        nearest_enemy.position[1] - controlled.position[1],
    )
    return action_vector[0] * enemy_vector[0] + action_vector[1] * enemy_vector[1] < 0.0


def _is_low_hp_chase(
    frame: ReplayFrame,
    controlled_agent_id: str,
    action_type: ActionType,
) -> bool:
    agents = _agent_by_id(frame)
    controlled = agents.get(controlled_agent_id)
    if controlled is None:
        return False
    low_hp_enemies = [
        agent
        for agent in agents.values()
        if agent.alive
        and agent.team_id != controlled.team_id
        and _safe_div(agent.hp, agent.max_hp) < 0.35
    ]
    target = _nearest_agent(controlled, low_hp_enemies)
    if target is None:
        return False
    action_vector = _action_vector(action_type)
    target_vector = (
        target.position[0] - controlled.position[0],
        target.position[1] - controlled.position[1],
    )
    return action_vector[0] * target_vector[0] + action_vector[1] * target_vector[1] > 0.0


def _is_ally_peel_target(
    frame: ReplayFrame,
    controlled_agent_id: str,
    target_intent_id: str,
) -> bool:
    agents = _agent_by_id(frame)
    controlled = agents.get(controlled_agent_id)
    if controlled is None:
        return False
    allies = [
        agent
        for agent in agents.values()
        if agent.alive
        and agent.agent_id != controlled_agent_id
        and agent.team_id == controlled.team_id
    ]
    if not allies:
        return False
    threatened_ally = min(allies, key=lambda ally: (_safe_div(ally.hp, ally.max_hp), ally.agent_id))
    enemies = [
        agent for agent in agents.values() if agent.alive and agent.team_id != controlled.team_id
    ]
    threat = _nearest_agent(threatened_ally, enemies)
    if threat is None or distance(threat.position, threatened_ally.position) > max(
        threat.attack_range, 8.0
    ):
        return False
    return threat.agent_id == target_intent_id


def _has_shared_target_intent(
    events: list[EventLog],
    controlled_agent_id: str,
    controlled_team_id: int,
    target_intent_id: str,
    frame: ReplayFrame | None,
) -> bool:
    if frame is None:
        return False
    agents = _agent_by_id(frame)
    for event in events:
        source_agent_id = event.source_agent_id
        if source_agent_id is None or source_agent_id == controlled_agent_id:
            continue
        source = agents.get(source_agent_id)
        if source is None or source.team_id != controlled_team_id:
            continue
        if _optional_str(event.payload.get("target_intent_id")) == target_intent_id:
            return True
    return False


def _action_events_by_tick(events: list[EventLog]) -> dict[int, list[EventLog]]:
    grouped: dict[int, list[EventLog]] = {}
    for event in events:
        if event.event_type == "agent_action_selected":
            grouped.setdefault(int(event.tick), []).append(event)
    return grouped


def _action_vector(action_type: ActionType) -> tuple[float, float]:
    vectors = {
        ActionType.MOVE_UP: (0.0, -1.0),
        ActionType.MOVE_DOWN: (0.0, 1.0),
        ActionType.MOVE_LEFT: (-1.0, 0.0),
        ActionType.MOVE_RIGHT: (1.0, 0.0),
        ActionType.MOVE_UP_LEFT: (-1.0, -1.0),
        ActionType.MOVE_UP_RIGHT: (1.0, -1.0),
        ActionType.MOVE_DOWN_LEFT: (-1.0, 1.0),
        ActionType.MOVE_DOWN_RIGHT: (1.0, 1.0),
    }
    return vectors.get(action_type, (0.0, 0.0))


def _controlled_action_events(events: list[EventLog], controlled_agent_id: str) -> list[EventLog]:
    return [
        event
        for event in events
        if event.event_type == "agent_action_selected"
        and event.source_agent_id == controlled_agent_id
    ]


def _scoreboard_value(frame: ReplayFrame, key: str) -> Any:
    if not isinstance(frame.scoreboard, dict):
        return None
    return frame.scoreboard.get(key)


def _float_payload(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_div(numerator: float | int, denominator: float | int) -> float:
    denominator_float = float(denominator)
    if denominator_float == 0.0:
        return 0.0
    result = float(numerator) / denominator_float
    return result if math.isfinite(result) else 0.0


def _optional_rate(numerator: float | int, denominator: float | int) -> float | None:
    if float(denominator) == 0.0:
        return None
    return _safe_div(numerator, denominator)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
