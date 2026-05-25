"""Small drawing helpers for the Pygame replay renderer."""

from __future__ import annotations

from typing import Any

from combatrl.renderer.camera import ReplayCamera
from combatrl.schemas.agent_state import AgentState

TEAM_COLORS = {
    0: (55, 126, 184),
    1: (228, 76, 72),
}
DEAD_COLOR = (95, 95, 95)


def draw_hp_bar(
    pygame: Any,
    surface: Any,
    camera: ReplayCamera,
    agent: AgentState,
) -> None:
    """Draw a compact HP bar above an agent."""
    px, py = camera.sim_to_screen(agent.position)
    width = 34
    height = 5
    x = px - width // 2
    y = py - 20
    fraction = 0.0 if agent.max_hp <= 0.0 else max(0.0, min(1.0, agent.hp / agent.max_hp))
    pygame.draw.rect(surface, (35, 35, 35), (x, y, width, height))
    pygame.draw.rect(surface, (72, 190, 104), (x, y, round(width * fraction), height))


def draw_attack_range(
    pygame: Any,
    surface: Any,
    camera: ReplayCamera,
    agent: AgentState,
) -> None:
    """Draw an attack range ring."""
    if not agent.alive:
        return
    pygame.draw.circle(
        surface,
        (120, 120, 120),
        camera.sim_to_screen(agent.position),
        camera.length_to_screen(agent.attack_range),
        1,
    )


def draw_velocity_vector(
    pygame: Any,
    surface: Any,
    camera: ReplayCamera,
    agent: AgentState,
) -> None:
    """Draw a velocity vector for a moving agent."""
    if agent.velocity == (0.0, 0.0):
        return
    start = camera.sim_to_screen(agent.position)
    end_position = (
        agent.position[0] + agent.velocity[0],
        agent.position[1] + agent.velocity[1],
    )
    pygame.draw.line(surface, (245, 183, 66), start, camera.sim_to_screen(end_position), 2)
