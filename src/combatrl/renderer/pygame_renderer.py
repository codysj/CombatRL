"""Local Pygame replay renderer."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from combatrl.renderer.camera import ReplayCamera
from combatrl.renderer.overlays import (
    DEAD_COLOR,
    TEAM_COLORS,
    draw_attack_range,
    draw_hp_bar,
    draw_velocity_vector,
)
from combatrl.replay.reader import ReplayReader
from combatrl.schemas.replay import ReplayFrame, ReplayMetadata

BACKGROUND = (24, 26, 28)
ARENA_FILL = (40, 44, 48)
ARENA_BORDER = (190, 190, 190)
TEXT_COLOR = (235, 235, 235)
TARGET_LINE_COLOR = (245, 183, 66)


def render_replay(
    replay_path: str,
    playback_speed: float = 1.0,
    overlays: list[str] | None = None,
    headless_smoke: bool = False,
) -> None:
    """Render saved replay frames and events without recomputing match logic."""
    if headless_smoke:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    try:
        import pygame
    except ModuleNotFoundError as exc:
        msg = "Install renderer extras with: uv sync --extra renderer"
        raise ModuleNotFoundError(msg) from exc

    reader = ReplayReader(Path(replay_path))
    metadata = reader.load_metadata()
    frames = reader.load_frames()
    if not frames:
        msg = "replay contains no frames"
        raise ValueError(msg)

    enabled_overlays = set(overlays or ["hp_bars", "attack_ranges", "target_lines"])
    playback_speed = max(0.1, playback_speed)
    tick_rate = metadata.tick_rate_hz
    screen_size = (1000, 720)

    pygame.init()
    try:
        surface = pygame.display.set_mode((1, 1) if headless_smoke else screen_size)
        if not headless_smoke:
            pygame.display.set_caption(f"CombatRL Replay - {metadata.match_id}")
        font = pygame.font.SysFont("consolas", 18)
        small_font = pygame.font.SysFont("consolas", 14)
        camera = _build_camera(metadata, surface.get_width(), surface.get_height())

        if headless_smoke:
            _draw_frame(
                pygame, surface, font, small_font, camera, metadata, frames[0], enabled_overlays
            )
            pygame.display.flip()
            return

        clock = pygame.time.Clock()
        frame_index = 0
        paused = False
        elapsed = 0.0
        running = True

        while running:
            dt_seconds = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key == pygame.K_RIGHT and paused:
                        frame_index = min(len(frames) - 1, frame_index + 1)
                    elif event.key == pygame.K_LEFT and paused:
                        frame_index = max(0, frame_index - 1)
                    elif event.key == pygame.K_1:
                        playback_speed = 1.0
                    elif event.key == pygame.K_2:
                        playback_speed = 2.0
                    elif event.key == pygame.K_4:
                        playback_speed = 4.0

            if not paused and frame_index < len(frames) - 1:
                elapsed += dt_seconds * playback_speed
                frame_duration = 1.0 / tick_rate
                while elapsed >= frame_duration and frame_index < len(frames) - 1:
                    frame_index += 1
                    elapsed -= frame_duration

            surface.fill(BACKGROUND)
            _draw_frame(
                pygame,
                surface,
                font,
                small_font,
                camera,
                metadata,
                frames[frame_index],
                enabled_overlays,
            )
            pygame.display.flip()
    finally:
        pygame.quit()


def _build_camera(metadata: ReplayMetadata, screen_width: int, screen_height: int) -> ReplayCamera:
    config = metadata.config
    arena_width = float(config.get("arena_width", 100.0))
    arena_height = float(config.get("arena_height", 60.0))
    return ReplayCamera(
        screen_width=screen_width,
        screen_height=screen_height,
        arena_width=arena_width,
        arena_height=arena_height,
    )


def _draw_frame(
    pygame: Any,
    surface: Any,
    font: Any,
    small_font: Any,
    camera: ReplayCamera,
    metadata: ReplayMetadata,
    frame: ReplayFrame,
    enabled_overlays: set[str],
) -> None:
    arena_rect = (
        round(camera.offset_x),
        round(camera.screen_height - camera.offset_y - camera.arena_height * camera.scale),
        round(camera.arena_width * camera.scale),
        round(camera.arena_height * camera.scale),
    )
    pygame.draw.rect(surface, ARENA_FILL, arena_rect)
    pygame.draw.rect(surface, ARENA_BORDER, arena_rect, 2)

    for obstacle in metadata.config.get("obstacles", []):
        _draw_obstacle(pygame, surface, camera, obstacle)

    if "attack_ranges" in enabled_overlays:
        for agent in frame.agents:
            draw_attack_range(pygame, surface, camera, agent)

    if "target_lines" in enabled_overlays:
        _draw_target_lines(pygame, surface, camera, frame)

    for agent in frame.agents:
        color = DEAD_COLOR if not agent.alive else TEAM_COLORS.get(agent.team_id, (180, 180, 180))
        pygame.draw.circle(surface, color, camera.sim_to_screen(agent.position), 9)
        pygame.draw.circle(surface, (20, 20, 20), camera.sim_to_screen(agent.position), 9, 1)
        if "hp_bars" in enabled_overlays:
            draw_hp_bar(pygame, surface, camera, agent)
        if "velocity_vectors" in enabled_overlays:
            draw_velocity_vector(pygame, surface, camera, agent)

    _draw_text(
        surface,
        font,
        f"tick={frame.tick} time={frame.sim_time_seconds:.2f}s match={metadata.match_id}",
        (18, 14),
    )
    _draw_text(
        surface,
        font,
        (
            f"team0 alive={frame.scoreboard.get('team0_alive')} "
            f"hp={float(frame.scoreboard.get('team0_total_hp') or 0.0):.1f} | "
            f"team1 alive={frame.scoreboard.get('team1_alive')} "
            f"hp={float(frame.scoreboard.get('team1_total_hp') or 0.0):.1f}"
        ),
        (18, 38),
    )
    _draw_event_feed(surface, small_font, frame)


def _draw_obstacle(pygame: Any, surface: Any, camera: ReplayCamera, obstacle: object) -> None:
    if not isinstance(obstacle, dict):
        return
    x = float(obstacle.get("x", 0.0))
    y = float(obstacle.get("y", 0.0))
    width = float(obstacle.get("width", 0.0))
    height = float(obstacle.get("height", 0.0))
    top_left = camera.sim_to_screen((x, y + height))
    rect = (
        top_left[0],
        top_left[1],
        camera.length_to_screen(width),
        camera.length_to_screen(height),
    )
    pygame.draw.rect(surface, (80, 82, 86), rect)
    pygame.draw.rect(surface, (130, 130, 130), rect, 1)


def _draw_target_lines(
    pygame: Any,
    surface: Any,
    camera: ReplayCamera,
    frame: ReplayFrame,
) -> None:
    agents_by_id = {agent.agent_id: agent for agent in frame.agents}
    for event in frame.events:
        if event.event_type != "agent_attacked":
            continue
        if event.source_agent_id not in agents_by_id or event.target_agent_id not in agents_by_id:
            continue
        source = agents_by_id[event.source_agent_id]
        target = agents_by_id[event.target_agent_id]
        pygame.draw.line(
            surface,
            TARGET_LINE_COLOR,
            camera.sim_to_screen(source.position),
            camera.sim_to_screen(target.position),
            2,
        )


def _draw_event_feed(surface: Any, font: Any, frame: ReplayFrame) -> None:
    recent_events = frame.events[-8:]
    y = surface.get_height() - 22 * max(1, len(recent_events)) - 12
    for event in recent_events:
        text = event.event_type
        if event.source_agent_id is not None:
            text += f" {event.source_agent_id}"
        if event.target_agent_id is not None:
            text += f" -> {event.target_agent_id}"
        _draw_text(surface, font, text, (18, y))
        y += 22


def _draw_text(surface: Any, font: Any, text: str, position: tuple[int, int]) -> None:
    surface.blit(font.render(text, True, TEXT_COLOR), position)
