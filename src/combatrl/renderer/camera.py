"""Coordinate transforms for replay rendering."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayCamera:
    """Convert bottom-left simulation coordinates to top-left screen coordinates."""

    screen_width: int
    screen_height: int
    arena_width: float
    arena_height: float
    margin: int = 40

    @property
    def scale(self) -> float:
        usable_width = max(1, self.screen_width - self.margin * 2)
        usable_height = max(1, self.screen_height - self.margin * 2)
        return min(usable_width / self.arena_width, usable_height / self.arena_height)

    @property
    def offset_x(self) -> float:
        return (self.screen_width - self.arena_width * self.scale) / 2.0

    @property
    def offset_y(self) -> float:
        return (self.screen_height - self.arena_height * self.scale) / 2.0

    def sim_to_screen(self, position: tuple[float, float]) -> tuple[int, int]:
        x, y = position
        screen_x = x * self.scale + self.offset_x
        screen_y = self.screen_height - (y * self.scale + self.offset_y)
        return round(screen_x), round(screen_y)

    def length_to_screen(self, value: float) -> int:
        return max(1, round(value * self.scale))
