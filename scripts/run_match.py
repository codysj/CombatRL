"""Run a headless CombatRL match to terminal timeout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from combatrl.schemas.configs import load_simulation_config
from combatrl.sim.engine import SimulationEngine

DEFAULT_CONFIG_PATH = Path("configs/env/mvp_2v2_elimination.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a headless CombatRL match.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-debug-invariants", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_simulation_config(args.config)
        engine = SimulationEngine(
            config=config,
            seed=args.seed,
            debug_invariants=not args.no_debug_invariants,
        )
        final_state = engine.run_until_terminal()
    except Exception as exc:
        print(f"run_match failed: {exc}", file=sys.stderr)
        return 1

    print(f"match_id: {final_state.match_id}")
    print(f"scenario_id: {config.scenario_id}")
    print(f"seed: {final_state.seed}")
    print(f"final_tick: {final_state.tick}")
    print(f"max_ticks: {final_state.max_ticks}")
    print(f"terminal: {str(final_state.terminal).lower()}")
    print(f"terminal_reason: {final_state.terminal_reason}")
    print(f"winner_team_id: {final_state.winner_team_id}")
    print(f"agent_count: {len(final_state.agents)}")
    print("agents:")
    for agent in sorted(final_state.agents.values(), key=lambda item: item.agent_id):
        print(f"  - {agent.agent_id}: team={agent.team_id}, role={agent.role}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
