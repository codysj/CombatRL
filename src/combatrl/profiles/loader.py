"""Load and validate behavior profiles from YAML."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError
from yaml import YAMLError

from combatrl.schemas.profiles import BehaviorProfile


def load_profile(path: str | Path) -> BehaviorProfile:
    """Load one behavior profile YAML file."""
    profile_path = Path(path)
    if not profile_path.exists():
        msg = f"profile file does not exist: {profile_path}"
        raise FileNotFoundError(msg)
    if not profile_path.is_file():
        msg = f"profile path is not a file: {profile_path}"
        raise ValueError(msg)

    try:
        with profile_path.open("r", encoding="utf-8") as file:
            raw_profile = yaml.safe_load(file)
    except YAMLError as exc:
        msg = f"invalid YAML in profile file {profile_path}: {exc}"
        raise ValueError(msg) from exc

    if raw_profile is None:
        msg = f"profile file is empty: {profile_path}"
        raise ValueError(msg)
    if not isinstance(raw_profile, dict):
        msg = f"profile file must contain a YAML mapping: {profile_path}"
        raise ValueError(msg)
    if "profile_schema_version" not in raw_profile:
        msg = f"invalid behavior profile {profile_path}: profile_schema_version is required"
        raise ValueError(msg)

    try:
        return BehaviorProfile.model_validate(raw_profile)
    except ValidationError as exc:
        msg = f"invalid behavior profile {profile_path}: {_format_validation_error(exc)}"
        raise ValueError(msg) from exc


def load_profile_by_id(
    profile_id: str,
    profiles_dir: str | Path = "configs/profiles",
) -> BehaviorProfile:
    """Load a profile from the configured profile preset directory."""
    normalized_id = profile_id.strip()
    if not normalized_id:
        msg = "profile_id must be non-empty"
        raise ValueError(msg)
    return load_profile(Path(profiles_dir) / f"{normalized_id}.yaml")


def list_profiles(profiles_dir: str | Path = "configs/profiles") -> list[str]:
    """List available profile preset IDs in stable order."""
    directory = Path(profiles_dir)
    if not directory.exists():
        msg = f"profiles directory does not exist: {directory}"
        raise FileNotFoundError(msg)
    if not directory.is_dir():
        msg = f"profiles path is not a directory: {directory}"
        raise ValueError(msg)
    return sorted(path.stem for path in directory.glob("*.yaml") if path.is_file())


def _format_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"])
        message = str(error["msg"])
        input_value: Any = error.get("input")
        if input_value is None:
            parts.append(f"{location}: {message}")
        else:
            parts.append(f"{location}: {message} (got {input_value!r})")
    return "; ".join(parts)
