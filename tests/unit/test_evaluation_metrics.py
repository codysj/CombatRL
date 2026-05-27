"""Evaluation metric tests from tiny synthetic replay data."""

import math

from combatrl.core.constants import REPLAY_SCHEMA_VERSION
from combatrl.evaluation.metrics import compute_match_metrics_from_frames_events
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.replay import EventLog, ReplayFrame, make_event_log


def test_core_metrics_from_synthetic_events() -> None:
    frames = _frames(winner_team_id=0, terminal_reason="elimination")
    events = [
        _action_event(1, "team0_ranged_dps_0", "ATTACK_NEAREST"),
        make_event_log(
            match_id="match",
            tick=1,
            index=1,
            event_type="agent_attacked",
            source_agent_id="team0_ranged_dps_0",
            target_agent_id="team1_ranged_dps_0",
            payload={},
        ),
        make_event_log(
            match_id="match",
            tick=1,
            index=2,
            event_type="agent_damaged",
            source_agent_id="team0_ranged_dps_0",
            target_agent_id="team1_ranged_dps_0",
            payload={"damage": 10.0},
        ),
        make_event_log(
            match_id="match",
            tick=2,
            index=0,
            event_type="agent_damaged",
            source_agent_id="team1_ranged_dps_0",
            target_agent_id="team0_ranged_dps_0",
            payload={"damage": 4.0},
        ),
        _action_event(2, "team0_ranged_dps_0", "MOVE_LEFT"),
    ]

    metrics = compute_match_metrics_from_frames_events(
        frames,
        events,
        "team0_ranged_dps_0",
    )

    assert metrics["damage_dealt"] == 10.0
    assert metrics["damage_taken"] == 4.0
    assert metrics["survival_ticks"] == 2
    assert metrics["win"] == 1
    assert metrics["loss"] == 0
    assert metrics["draw_or_timeout"] == 0
    assert math.isfinite(float(metrics["avg_distance_to_ally"]))
    assert math.isfinite(float(metrics["avg_distance_to_nearest_enemy"]))
    assert metrics["attack_action_rate"] == 0.5
    assert metrics["retreat_action_rate"] == 0.5


def test_timeout_and_missing_optional_fields_do_not_crash() -> None:
    frames = _frames(winner_team_id=None, terminal_reason="timeout")
    events = [_action_event(1, "team0_ranged_dps_0", "NO_OP", payload={})]

    metrics = compute_match_metrics_from_frames_events(
        frames,
        events,
        "team0_ranged_dps_0",
    )

    assert metrics["draw_or_timeout"] == 1
    assert metrics["no_op_rate"] == 1.0
    assert metrics["shared_target_rate"] == 0.0
    assert metrics["low_hp_chase_rate"] == 0.0


def _frames(winner_team_id: int | None, terminal_reason: str | None) -> list[ReplayFrame]:
    return [
        _frame(0, winner_team_id=None, terminal_reason=None, controlled_hp=90.0),
        _frame(1, winner_team_id=None, terminal_reason=None, controlled_hp=86.0),
        _frame(
            2, winner_team_id=winner_team_id, terminal_reason=terminal_reason, controlled_hp=86.0
        ),
    ]


def _frame(
    tick: int,
    *,
    winner_team_id: int | None,
    terminal_reason: str | None,
    controlled_hp: float,
) -> ReplayFrame:
    return ReplayFrame(
        replay_schema_version=REPLAY_SCHEMA_VERSION,
        match_id="match",
        tick=tick,
        sim_time_seconds=float(tick) / 20.0,
        agents=[
            _agent("team0_ranged_dps_0", 0, (20.0 - tick, 30.0), controlled_hp),
            _agent("team0_tank_0", 0, (22.0, 30.0), 160.0),
            _agent("team1_ranged_dps_0", 1, (30.0, 30.0), 80.0),
        ],
        events=[],
        scoreboard={
            "team0_alive": 2,
            "team1_alive": 1,
            "team0_total_hp": controlled_hp + 160.0,
            "team1_total_hp": 80.0,
            "winner_team_id": winner_team_id,
            "terminal_reason": terminal_reason,
        },
    )


def _agent(agent_id: str, team_id: int, position: tuple[float, float], hp: float) -> AgentState:
    return AgentState(
        agent_id=agent_id,
        team_id=team_id,
        role="ranged_dps" if "ranged" in agent_id else "tank",
        position=position,
        velocity=(0.0, 0.0),
        hp=hp,
        max_hp=90.0 if "ranged" in agent_id else 160.0,
        alive=hp > 0.0,
        movement_speed=3.0,
        attack_range=18.0,
        attack_damage=10.0,
        attack_cooldown_ticks=0,
        attack_cooldown_max_ticks=12,
        ability_cooldown_ticks=0,
        facing_vector=(1.0, 0.0),
        status_effects=[],
        current_target_id=None,
        last_action_id=None,
    )


def _action_event(
    tick: int,
    agent_id: str,
    action_type: str,
    payload: dict[str, object] | None = None,
) -> EventLog:
    merged_payload = {
        "action_type": action_type,
        "policy_id": "test",
        "valid": True,
        "fallback_used": False,
    }
    if payload is not None:
        merged_payload.update(payload)
    return make_event_log(
        match_id="match",
        tick=tick,
        index=0,
        event_type="agent_action_selected",
        source_agent_id=agent_id,
        payload=merged_payload,
    )
