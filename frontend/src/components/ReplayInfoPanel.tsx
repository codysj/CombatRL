import type { AgentSnapshot, ReplayMetadata, ReplaySummary } from "../replay/types";

interface ReplayInfoPanelProps {
  metadata: ReplayMetadata;
  summary: ReplaySummary;
  selectedAgent?: AgentSnapshot;
}

function roleLabel(role: string): string {
  return role.replaceAll("_", " ");
}

export function ReplayInfoPanel({ metadata, summary, selectedAgent }: ReplayInfoPanelProps) {
  return (
    <section className="panel info-panel">
      <div className="panel-heading">
        <h2>Replay intel</h2>
        <span>schema {metadata.replay_schema_version}</span>
      </div>
      <dl className="metadata-grid">
        <div><dt>Scenario</dt><dd>{metadata.scenario_id}</dd></div>
        <div><dt>Seed</dt><dd>{metadata.seed}</dd></div>
        <div><dt>Tick rate</dt><dd>{metadata.tick_rate_hz} Hz</dd></div>
        <div><dt>Result</dt><dd>{summary.winner_team_id === null ? "Draw" : `Team ${summary.winner_team_id}`}</dd></div>
      </dl>

      <div className="score-strip">
        <div className="score-team score-team-0">
          <span>Team 0</span>
          <strong>{summary.team0_alive} alive</strong>
        </div>
        <div className="score-team score-team-1">
          <span>Team 1</span>
          <strong>{summary.team1_alive} alive</strong>
        </div>
      </div>

      {selectedAgent ? (
        <div className="agent-card">
          <p className="eyebrow">Selected unit</p>
          <h3>{selectedAgent.agent_id}</h3>
          <div className="agent-stats">
            <span>{roleLabel(selectedAgent.role)}</span>
            <span>{Math.round(selectedAgent.hp)} / {Math.round(selectedAgent.max_hp)} HP</span>
            <span>Range {selectedAgent.attack_range?.toFixed(1) ?? "n/a"}</span>
            <span>{selectedAgent.alive ? "Active" : "Eliminated"}</span>
          </div>
        </div>
      ) : (
        <p className="selection-hint">Select a unit in the arena for current combat details.</p>
      )}
    </section>
  );
}
