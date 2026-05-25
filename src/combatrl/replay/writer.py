"""File-based replay writer."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from combatrl import __version__
from combatrl.core.constants import REPLAY_SCHEMA_VERSION
from combatrl.schemas.configs import SimulationConfig
from combatrl.schemas.match_state import MatchState
from combatrl.schemas.replay import EventLog, ReplayFrame, ReplayMetadata, ReplaySummary


def stable_config_hash(config: SimulationConfig) -> str:
    """Hash a config using deterministic JSON serialization."""
    payload = json.dumps(
        config.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ReplayWriter:
    """Write replay metadata, frames, events, and summary files."""

    def __init__(
        self,
        output_root: str | Path = "artifacts/replays",
        replay_schema_version: str = REPLAY_SCHEMA_VERSION,
        frame_interval: int = 1,
        use_timestamp: bool = True,
    ) -> None:
        if frame_interval <= 0:
            msg = "frame_interval must be positive"
            raise ValueError(msg)
        self.output_root = Path(output_root)
        self.replay_schema_version = replay_schema_version
        self.frame_interval = frame_interval
        self.use_timestamp = use_timestamp
        self.replay_path: Path | None = None
        self.metadata: ReplayMetadata | None = None
        self.frame_count = 0
        self.event_count = 0
        self._frames_file: TextIO | None = None
        self._events_file: TextIO | None = None

    def start_match(self, config: SimulationConfig, state: MatchState, seed: int) -> Path:
        """Create the replay directory and write metadata.json."""
        self.output_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        directory_name = f"{config.scenario_id}_seed-{seed}"
        if self.use_timestamp:
            directory_name = f"{timestamp}_{directory_name}"
        self.replay_path = self.output_root / directory_name
        self.replay_path.mkdir(parents=True, exist_ok=True)

        self.metadata = ReplayMetadata(
            replay_schema_version=self.replay_schema_version,
            match_id=state.match_id,
            scenario_id=config.scenario_id,
            seed=seed,
            config=config.model_dump(mode="json"),
            config_hash=stable_config_hash(config),
            tick_rate_hz=config.tick_rate_hz,
            decision_rate_hz=None,
            created_at_utc=datetime.now(UTC).isoformat(),
            combatrl_version=__version__,
        )
        self._write_json(self.replay_path / "metadata.json", self.metadata.model_dump(mode="json"))
        self._frames_file = (self.replay_path / "frames.jsonl").open("w", encoding="utf-8")
        self._events_file = (self.replay_path / "events.jsonl").open("w", encoding="utf-8")
        return self.replay_path

    def write_frame(self, frame: ReplayFrame) -> None:
        """Append one ReplayFrame JSON object to frames.jsonl."""
        if self._frames_file is None:
            msg = "start_match must be called before write_frame"
            raise RuntimeError(msg)
        self._frames_file.write(self._to_json_line(frame.model_dump(mode="json")))
        self.frame_count += 1

    def write_events(self, events: list[EventLog]) -> None:
        """Append EventLog JSON objects to events.jsonl."""
        if self._events_file is None:
            msg = "start_match must be called before write_events"
            raise RuntimeError(msg)
        for event in events:
            self._events_file.write(self._to_json_line(event.model_dump(mode="json")))
            self.event_count += 1

    def finish(self, summary: ReplaySummary) -> Path:
        """Write summary.json and close open file handles."""
        if self.replay_path is None:
            msg = "start_match must be called before finish"
            raise RuntimeError(msg)
        self.close()
        self._write_json(self.replay_path / "summary.json", summary.model_dump(mode="json"))
        return self.replay_path

    def close(self) -> None:
        """Close file handles safely."""
        for file in (self._frames_file, self._events_file):
            if file is not None and not file.closed:
                file.close()
        self._frames_file = None
        self._events_file = None

    @staticmethod
    def _to_json_line(payload: dict[str, object]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"

    @staticmethod
    def _write_json(path: Path, payload: dict[str, object]) -> None:
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
