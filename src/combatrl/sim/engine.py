"""Deterministic headless simulator engine."""

from combatrl.core.constants import ROLE_COMBAT_STATS
from combatrl.core.geometry import (
    clamp_position,
    distance,
    normalize_vector,
    scale_vector,
)
from combatrl.core.rng import ProjectRNG
from combatrl.schemas.actions import ActionCommand, ActionType
from combatrl.schemas.agent_state import AgentState
from combatrl.schemas.configs import SimulationConfig
from combatrl.schemas.match_state import MatchState, ObstacleState
from combatrl.schemas.replay import EventLog, make_event_log
from combatrl.sim.invariants import validate_match_state

MOVEMENT_DIRECTIONS: dict[ActionType, tuple[float, float]] = {
    ActionType.MOVE_UP: (0.0, -1.0),
    ActionType.MOVE_DOWN: (0.0, 1.0),
    ActionType.MOVE_LEFT: (-1.0, 0.0),
    ActionType.MOVE_RIGHT: (1.0, 0.0),
    ActionType.MOVE_UP_LEFT: (-1.0, -1.0),
    ActionType.MOVE_UP_RIGHT: (1.0, -1.0),
    ActionType.MOVE_DOWN_LEFT: (-1.0, 1.0),
    ActionType.MOVE_DOWN_RIGHT: (1.0, 1.0),
}


class SimulationEngine:
    """Owns authoritative match state and deterministic tick progression."""

    def __init__(self, config: SimulationConfig, seed: int, debug_invariants: bool = True) -> None:
        self.config = config
        self.rng = ProjectRNG(seed)
        self.debug_invariants = debug_invariants
        self._state = self.initialize_state()
        self._last_events: list[EventLog] = []

    @property
    def state(self) -> MatchState:
        """Current authoritative match state."""
        return self._state

    @property
    def last_events(self) -> list[EventLog]:
        """Events emitted by the most recent step."""
        return list(self._last_events)

    def initialize_state(self) -> MatchState:
        """Create a deterministic initial state from the simulation config."""
        agents: dict[str, AgentState] = {}
        for team in self.config.teams:
            for agent_config in team.agents:
                role_stats = ROLE_COMBAT_STATS[agent_config.role]
                agents[agent_config.agent_id] = AgentState(
                    agent_id=agent_config.agent_id,
                    team_id=agent_config.team_id,
                    role=agent_config.role,
                    position=agent_config.spawn_position,
                    velocity=(0.0, 0.0),
                    hp=role_stats.max_hp,
                    max_hp=role_stats.max_hp,
                    alive=True,
                    movement_speed=role_stats.movement_speed,
                    attack_range=role_stats.attack_range,
                    attack_damage=role_stats.attack_damage,
                    attack_cooldown_ticks=0,
                    attack_cooldown_max_ticks=role_stats.attack_cooldown_ticks,
                    ability_cooldown_ticks=0,
                    facing_vector=(1.0, 0.0),
                    status_effects=[],
                    current_target_id=None,
                    last_action_id=None,
                )

        state = MatchState(
            match_id=f"{self.config.scenario_id}_seed_{self.rng.seed}",
            seed=self.rng.seed,
            tick=0,
            max_ticks=self.config.max_ticks,
            tick_rate_hz=self.config.tick_rate_hz,
            arena_width=self.config.arena_width,
            arena_height=self.config.arena_height,
            agents=agents,
            obstacles=[
                ObstacleState(
                    obstacle_id=obstacle.obstacle_id,
                    x=obstacle.x,
                    y=obstacle.y,
                    width=obstacle.width,
                    height=obstacle.height,
                )
                for obstacle in self.config.obstacles
            ],
            terminal=False,
            winner_team_id=None,
            terminal_reason=None,
        )

        if self.debug_invariants:
            validate_match_state(state)
        return state

    def step(
        self,
        actions: list[ActionCommand] | None = None,
        action_metadata: dict[str, dict[str, object]] | None = None,
    ) -> MatchState:
        """Advance one fixed timestep.

        Tick order is:
        validate actions, resolve movement, resolve attacks, apply deaths,
        decrement cooldowns, evaluate terminal state, increment tick, validate invariants.
        """
        if self._state.terminal:
            self._last_events = []
            return self._state

        action_by_agent_id = self._action_map(actions)
        action_metadata = {} if action_metadata is None else action_metadata
        event_tick = self._state.tick + 1
        events: list[EventLog] = []
        cooldowns_before_attacks = {
            agent_id: agent.attack_cooldown_ticks for agent_id, agent in self._state.agents.items()
        }

        for agent_id in sorted(self._state.agents):
            event_payload: dict[str, object] = {"action_type": action_by_agent_id[agent_id].value}
            event_payload.update(action_metadata.get(agent_id, {}))
            self._append_event(
                events=events,
                tick=event_tick,
                event_type="agent_action_selected",
                source_agent_id=agent_id,
                payload=event_payload,
            )

        self._resolve_movement(action_by_agent_id, events, event_tick)
        attacked_agent_ids, eliminated_by = self._resolve_attacks(
            action_by_agent_id,
            events,
            event_tick,
        )
        self._apply_deaths(events, event_tick, eliminated_by)
        self._decrement_cooldowns(cooldowns_before_attacks, attacked_agent_ids)
        self._evaluate_elimination()

        next_tick = self._state.tick + 1
        if not self._state.terminal and next_tick >= self._state.max_ticks:
            self._state.terminal = True
            self._state.terminal_reason = "timeout"
            self._state.winner_team_id = None

        self._state.tick = next_tick
        if self._state.terminal:
            self._append_event(
                events=events,
                tick=self._state.tick,
                event_type="match_ended",
                payload={
                    "terminal_reason": self._state.terminal_reason,
                    "winner_team_id": self._state.winner_team_id,
                },
            )

        if self.debug_invariants:
            validate_match_state(self._state)
        self._last_events = events
        return self._state

    def run_until_terminal(self) -> MatchState:
        """Run ticks until the match reaches a terminal state."""
        while not self._state.terminal:
            self.step()
        return self._state

    def _action_map(self, actions: list[ActionCommand] | None) -> dict[str, ActionType]:
        action_by_agent_id = {agent_id: ActionType.NO_OP for agent_id in sorted(self._state.agents)}
        if actions is None:
            return action_by_agent_id

        for action in actions:
            if action.agent_id in action_by_agent_id:
                action_by_agent_id[action.agent_id] = action.action_type
        return action_by_agent_id

    def _resolve_movement(
        self,
        action_by_agent_id: dict[str, ActionType],
        events: list[EventLog],
        event_tick: int,
    ) -> None:
        dt = 1.0 / self._state.tick_rate_hz
        for agent_id in sorted(self._state.agents):
            agent = self._state.agents[agent_id]
            if not agent.alive:
                agent.velocity = (0.0, 0.0)
                continue

            raw_direction = MOVEMENT_DIRECTIONS.get(action_by_agent_id[agent_id])
            if raw_direction is None:
                agent.velocity = (0.0, 0.0)
                continue

            direction = normalize_vector(raw_direction)
            velocity = scale_vector(direction, agent.movement_speed)
            previous_position = agent.position
            next_position = (
                agent.position[0] + velocity[0] * dt,
                agent.position[1] + velocity[1] * dt,
            )
            agent.position = clamp_position(
                next_position,
                self._state.arena_width,
                self._state.arena_height,
            )
            agent.velocity = velocity
            agent.facing_vector = direction
            if agent.position != previous_position:
                self._append_event(
                    events=events,
                    tick=event_tick,
                    event_type="agent_moved",
                    source_agent_id=agent.agent_id,
                    payload={
                        "from_position": previous_position,
                        "to_position": agent.position,
                        "velocity": agent.velocity,
                    },
                )

    def _resolve_attacks(
        self,
        action_by_agent_id: dict[str, ActionType],
        events: list[EventLog],
        event_tick: int,
    ) -> tuple[set[str], dict[str, str]]:
        attacked_agent_ids: set[str] = set()
        eliminated_by: dict[str, str] = {}
        for agent_id in sorted(self._state.agents):
            attacker = self._state.agents[agent_id]
            if (
                not attacker.alive
                or action_by_agent_id[agent_id] != ActionType.ATTACK_NEAREST
                or attacker.attack_cooldown_ticks > 0
            ):
                continue

            target = self._nearest_alive_enemy_in_range(attacker)
            if target is None:
                continue

            hp_before = target.hp
            target.hp = max(0.0, target.hp - attacker.attack_damage)
            attacker.attack_cooldown_ticks = attacker.attack_cooldown_max_ticks
            attacker.current_target_id = target.agent_id
            attacked_agent_ids.add(agent_id)
            self._append_event(
                events=events,
                tick=event_tick,
                event_type="agent_attacked",
                source_agent_id=attacker.agent_id,
                target_agent_id=target.agent_id,
                payload={
                    "attack_damage": attacker.attack_damage,
                    "target_hp_before": hp_before,
                    "target_hp_after": target.hp,
                },
            )
            self._append_event(
                events=events,
                tick=event_tick,
                event_type="agent_damaged",
                source_agent_id=attacker.agent_id,
                target_agent_id=target.agent_id,
                payload={
                    "damage": hp_before - target.hp,
                    "hp_before": hp_before,
                    "hp_after": target.hp,
                },
            )
            self._append_event(
                events=events,
                tick=event_tick,
                event_type="cooldown_started",
                source_agent_id=attacker.agent_id,
                payload={
                    "cooldown": "attack",
                    "cooldown_ticks": attacker.attack_cooldown_ticks,
                },
            )
            if target.hp <= 0.0:
                eliminated_by[target.agent_id] = attacker.agent_id

        return attacked_agent_ids, eliminated_by

    def _nearest_alive_enemy_in_range(self, attacker: AgentState) -> AgentState | None:
        candidates = [
            agent
            for agent in self._state.agents.values()
            if agent.alive
            and agent.team_id != attacker.team_id
            and distance(attacker.position, agent.position) <= attacker.attack_range
        ]
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda target: (distance(attacker.position, target.position), target.agent_id),
        )

    def _apply_deaths(
        self,
        events: list[EventLog],
        event_tick: int,
        eliminated_by: dict[str, str],
    ) -> None:
        for agent in sorted(self._state.agents.values(), key=lambda item: item.agent_id):
            if agent.hp <= 0.0:
                was_alive = agent.alive
                agent.hp = 0.0
                agent.alive = False
                agent.velocity = (0.0, 0.0)
                if was_alive:
                    self._append_event(
                        events=events,
                        tick=event_tick,
                        event_type="agent_eliminated",
                        source_agent_id=eliminated_by.get(agent.agent_id),
                        target_agent_id=agent.agent_id,
                        payload={},
                    )

    def _decrement_cooldowns(
        self,
        cooldowns_before_attacks: dict[str, int],
        attacked_agent_ids: set[str],
    ) -> None:
        for agent_id, agent in self._state.agents.items():
            if agent_id in attacked_agent_ids:
                continue
            if cooldowns_before_attacks[agent_id] > 0:
                agent.attack_cooldown_ticks = max(0, agent.attack_cooldown_ticks - 1)
            if agent.ability_cooldown_ticks > 0:
                agent.ability_cooldown_ticks -= 1

    def _evaluate_elimination(self) -> None:
        alive_team_ids = {agent.team_id for agent in self._state.agents.values() if agent.alive}
        all_team_ids = {agent.team_id for agent in self._state.agents.values()}
        if len(all_team_ids) <= 1 or len(alive_team_ids) == len(all_team_ids):
            return

        self._state.terminal = True
        self._state.terminal_reason = "elimination"
        self._state.winner_team_id = (
            next(iter(alive_team_ids)) if len(alive_team_ids) == 1 else None
        )

    def _append_event(
        self,
        *,
        events: list[EventLog],
        tick: int,
        event_type: str,
        source_agent_id: str | None = None,
        target_agent_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        events.append(
            make_event_log(
                match_id=self._state.match_id,
                tick=tick,
                index=len(events),
                event_type=event_type,
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                payload=payload,
            )
        )
