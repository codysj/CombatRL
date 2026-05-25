"""Replay file reader."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from combatrl.schemas.replay import EventLog, ReplayFrame, ReplayMetadata, ReplaySummary


class ReplayReader:
    """Read a replay directory or one of its core files."""

    def __init__(self, replay_path: str | Path) -> None:
        self.replay_path = self._resolve_replay_dir(Path(replay_path))

    def load_metadata(self) -> ReplayMetadata:
        return ReplayMetadata.model_validate(self._read_json("metadata.json"))

    def iter_frames(self) -> Iterator[ReplayFrame]:
        yield from self._iter_jsonl("frames.jsonl", ReplayFrame)

    def load_frames(self) -> list[ReplayFrame]:
        return list(self.iter_frames())

    def iter_events(self) -> Iterator[EventLog]:
        yield from self._iter_jsonl("events.jsonl", EventLog)

    def load_events(self) -> list[EventLog]:
        return list(self.iter_events())

    def load_summary(self) -> ReplaySummary:
        return ReplaySummary.model_validate(self._read_json("summary.json"))

    @staticmethod
    def _resolve_replay_dir(path: Path) -> Path:
        if path.is_file() and path.name in {"metadata.json", "frames.jsonl", "events.jsonl"}:
            return path.parent
        return path

    def _read_json(self, filename: str) -> dict[str, object]:
        path = self.replay_path / filename
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            msg = f"{filename} must contain a JSON object"
            raise ValueError(msg)
        return data

    def _iter_jsonl[T](self, filename: str, model_type: type[T]) -> Iterator[T]:
        path = self.replay_path / filename
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    msg = f"{filename}:{line_number} invalid JSON: {exc}"
                    raise ValueError(msg) from exc
                yield model_type.model_validate(payload)  # type: ignore[attr-defined]
