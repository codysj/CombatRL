"""Minimal deterministic headless simulator engine for Phase P1."""

from typing import Final

from combatrl.core.rng import ProjectRNG
from combatrl.schemas.agent_state import AgentState, RoleName
from combatrl.schemas.configs import SimulationConfig
from combatrl.schemas.match_state import MatchState, ObstacleState
from combatrl.sim.invariants import validate_match_state

ROLE_MAX_HP: Final[dict[RoleName, float]] = {
    "tank": 160.0,
    "ranged_dps": 90.0,
    "support": 80.0,
}


class SimulationEngine:
    """Owns authoritative match state and deterministic tick progression."""

    def __init__(self, config: SimulationConfig, seed: int, debug_invariants: bool = True) -> None:
        self.config = config
        self.rng = ProjectRNG(seed)
        self.debug_invariants = debug_invariants
        self._state = self.initialize_state()

    @property
    def state(self) -> MatchState:
        """Current authoritative match state."""
        return self._state

    def initialize_state(self) -> MatchState:
        """Create a deterministic initial state from the simulation config."""
        agents: dict[str, AgentState] = {}
        for team in self.config.teams:
            for agent_config in team.agents:
                max_hp = ROLE_MAX_HP[agent_config.role]
                agents[agent_config.agent_id] = AgentState(
                    agent_id=agent_config.agent_id,
                    team_id=agent_config.team_id,
                    role=agent_config.role,
                    position=agent_config.spawn_position,
                    velocity=(0.0, 0.0),
                    hp=max_hp,
                    max_hp=max_hp,
                    alive=True,
                    attack_cooldown_ticks=0,
                    ability_cooldown_ticks=0,
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

    def step(self) -> MatchState:
        """Advance one deterministic P1 tick with no movement or combat."""
        if self._state.terminal:
            return self._state

        self._state.tick += 1
        if self._state.tick >= self._state.max_ticks:
            self._state.terminal = True
            self._state.terminal_reason = "timeout"
            self._state.winner_team_id = None

        if self.debug_invariants:
            validate_match_state(self._state)
        return self._state

    def run_until_terminal(self) -> MatchState:
        """Run ticks until the match reaches a terminal state."""
        while not self._state.terminal:
            self.step()
        return self._state
