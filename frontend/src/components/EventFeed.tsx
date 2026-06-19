import type { ReplayEvent } from "../replay/types";

interface EventFeedProps {
  events: ReplayEvent[];
}

const DISPLAYED_TYPES = new Set([
  "match_started",
  "agent_attacked",
  "agent_damaged",
  "agent_eliminated",
  "match_ended",
]);

function eventDescription(event: ReplayEvent): string {
  const source = event.source_agent_id?.replaceAll("_", " ") ?? "Match";
  const target = event.target_agent_id?.replaceAll("_", " ");
  switch (event.event_type) {
    case "agent_attacked":
      return `${source} attacked ${target ?? "a target"}`;
    case "agent_damaged":
      return `${target ?? "Agent"} took ${String(event.payload.damage ?? "?")} damage`;
    case "agent_eliminated":
      return `${target ?? source} was eliminated`;
    case "match_ended":
      return `Match ended: ${String(event.payload.terminal_reason ?? "complete")}`;
    case "match_started":
      return "Match started";
    default:
      return event.event_type.replaceAll("_", " ");
  }
}

export function filterFeedEvents(events: ReplayEvent[]): ReplayEvent[] {
  return events.filter((event) => DISPLAYED_TYPES.has(event.event_type));
}

export function EventFeed({ events }: EventFeedProps) {
  return (
    <section className="panel event-panel">
      <div className="panel-heading">
        <h2>Combat log</h2>
        <span>live</span>
      </div>
      <div className="event-list">
        {events.length === 0 ? (
          <p className="muted">No combat events at this time.</p>
        ) : (
          events.map((event) => (
            <div className={`event-row event-${event.event_type}`} key={event.event_id}>
              <time>T{event.tick}</time>
              <p>{eventDescription(event)}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
