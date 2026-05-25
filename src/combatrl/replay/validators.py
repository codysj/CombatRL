"""Replay validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from combatrl.replay.reader import ReplayReader


class ReplayValidationError(Exception):
    """Raised when a replay artifact is invalid."""


def validate_replay(replay_path: str | Path) -> None:
    """Validate a replay artifact, raising on the first error."""
    report = validate_replay_report(replay_path)
    if not report["valid"]:
        raise ReplayValidationError(str(report["error"]))


def validate_replay_report(replay_path: str | Path) -> dict[str, Any]:
    """Validate a replay artifact and return a concise report."""
    try:
        path = ReplayReader._resolve_replay_dir(Path(replay_path))
        _validate_replay_dir(path)
        reader = ReplayReader(path)
        metadata = reader.load_metadata()
        summary = reader.load_summary()
        frames = reader.load_frames()
        events = reader.load_events()

        _validate_frame_sequence(frames, summary.final_tick)
        _validate_counts(frames, events, summary)
        _validate_events(frames, events)
        _validate_terminal_summary(frames, summary)

        return {
            "valid": True,
            "match_id": metadata.match_id,
            "scenario_id": metadata.scenario_id,
            "frames": len(frames),
            "events": len(events),
            "final_tick": summary.final_tick,
            "terminal_reason": summary.terminal_reason,
            "winner_team_id": summary.winner_team_id,
            "error": None,
        }
    except (OSError, ValueError, ValidationError, ReplayValidationError) as exc:
        return {
            "valid": False,
            "match_id": None,
            "scenario_id": None,
            "frames": 0,
            "events": 0,
            "final_tick": None,
            "terminal_reason": None,
            "winner_team_id": None,
            "error": str(exc),
        }


def _validate_replay_dir(path: Path) -> None:
    if not path.exists():
        msg = f"replay directory does not exist: {path}"
        raise ReplayValidationError(msg)
    if not path.is_dir():
        msg = f"replay path is not a directory: {path}"
        raise ReplayValidationError(msg)
    for filename in ("metadata.json", "frames.jsonl", "events.jsonl", "summary.json"):
        if not (path / filename).exists():
            msg = f"missing required replay file: {filename}"
            raise ReplayValidationError(msg)


def _validate_frame_sequence(frames: list[Any], final_tick: int) -> None:
    if not frames:
        msg = "frames.jsonl must contain at least one frame"
        raise ReplayValidationError(msg)

    if frames[0].tick != 0:
        msg = f"first frame tick must be 0, got {frames[0].tick}"
        raise ReplayValidationError(msg)

    previous_tick = -1
    for frame in frames:
        if frame.tick <= previous_tick:
            msg = (
                f"frame ticks must be strictly increasing: tick {frame.tick} after {previous_tick}"
            )
            raise ReplayValidationError(msg)
        previous_tick = frame.tick

    if frames[-1].tick != final_tick:
        msg = f"final frame tick {frames[-1].tick} does not match summary.final_tick {final_tick}"
        raise ReplayValidationError(msg)


def _validate_counts(frames: list[Any], events: list[Any], summary: Any) -> None:
    if summary.frame_count != len(frames):
        msg = f"summary.frame_count {summary.frame_count} does not match {len(frames)} frames"
        raise ReplayValidationError(msg)
    if summary.event_count != len(events):
        msg = f"summary.event_count {summary.event_count} does not match {len(events)} events"
        raise ReplayValidationError(msg)


def _validate_events(frames: list[Any], events: list[Any]) -> None:
    min_tick = frames[0].tick
    max_tick = frames[-1].tick
    agent_ids = {agent.agent_id for frame in frames for agent in frame.agents}
    event_ids: set[str] = set()

    for frame in frames:
        for event in frame.events:
            if event.tick != frame.tick:
                msg = (
                    f"frame tick {frame.tick} contains event {event.event_id} for tick {event.tick}"
                )
                raise ReplayValidationError(msg)

    for event in events:
        if event.event_id in event_ids:
            msg = f"duplicate event_id: {event.event_id}"
            raise ReplayValidationError(msg)
        event_ids.add(event.event_id)

        if event.tick < min_tick or event.tick > max_tick:
            msg = f"event {event.event_id} tick {event.tick} outside frame range"
            raise ReplayValidationError(msg)
        if event.source_agent_id is not None and event.source_agent_id not in agent_ids:
            msg = f"event {event.event_id} references unknown source {event.source_agent_id}"
            raise ReplayValidationError(msg)
        if event.target_agent_id is not None and event.target_agent_id not in agent_ids:
            msg = f"event {event.event_id} references unknown target {event.target_agent_id}"
            raise ReplayValidationError(msg)


def _validate_terminal_summary(frames: list[Any], summary: Any) -> None:
    final_scoreboard = frames[-1].scoreboard
    if (
        bool(summary.terminal)
        and final_scoreboard.get("terminal_reason") != summary.terminal_reason
    ):
        msg = (
            "summary terminal_reason does not match final frame scoreboard: "
            f"{summary.terminal_reason!r} != {final_scoreboard.get('terminal_reason')!r}"
        )
        raise ReplayValidationError(msg)
    if final_scoreboard.get("winner_team_id") != summary.winner_team_id:
        msg = (
            "summary winner_team_id does not match final frame scoreboard: "
            f"{summary.winner_team_id!r} != {final_scoreboard.get('winner_team_id')!r}"
        )
        raise ReplayValidationError(msg)
