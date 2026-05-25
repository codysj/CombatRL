"""Project-wide constants."""

from dataclasses import dataclass
from typing import Literal

RoleName = Literal["tank", "ranged_dps", "support"]

CONFIG_SCHEMA_VERSION = "1.0"
REPLAY_SCHEMA_VERSION = "1.0"
ACTION_SCHEMA_VERSION = "1.0"
OBSERVATION_SCHEMA_VERSION = "1.0"
PROFILE_SCHEMA_VERSION = "1.0"
METRICS_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class RoleCombatStats:
    """Static combat and movement stats for a configured role."""

    max_hp: float
    movement_speed: float
    attack_range: float
    attack_damage: float
    attack_cooldown_ticks: int


ROLE_COMBAT_STATS: dict[RoleName, RoleCombatStats] = {
    "tank": RoleCombatStats(
        max_hp=160.0,
        movement_speed=2.2,
        attack_range=8.0,
        attack_damage=14.0,
        attack_cooldown_ticks=16,
    ),
    "ranged_dps": RoleCombatStats(
        max_hp=90.0,
        movement_speed=3.0,
        attack_range=18.0,
        attack_damage=10.0,
        attack_cooldown_ticks=12,
    ),
    "support": RoleCombatStats(
        max_hp=80.0,
        movement_speed=2.8,
        attack_range=14.0,
        attack_damage=5.0,
        attack_cooldown_ticks=18,
    ),
}
