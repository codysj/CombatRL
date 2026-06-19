import { useEffect, useMemo, useState } from "react";

import { EventFeed, filterFeedEvents } from "./components/EventFeed";
import { ReplayControls } from "./components/ReplayControls";
import { ReplayInfoPanel } from "./components/ReplayInfoPanel";
import { frameAtTime } from "./replay/interpolate";
import { loadReplay } from "./replay/loadReplay";
import { eventsThroughTick, recentEvents, replayDuration } from "./replay/replayTimeline";
import type { ReplayBundle } from "./replay/types";
import { ArenaScene, type CameraMode } from "./render3d/ArenaScene";

const DEMO_REPLAY_URL = "/demo-replays/close-2v2";

export default function App() {
  const [replay, setReplay] = useState<ReplayBundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [cameraMode, setCameraMode] = useState<CameraMode>("angled");
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [showRanges, setShowRanges] = useState(true);
  const [showTargets, setShowTargets] = useState(true);

  useEffect(() => {
    let active = true;
    loadReplay(DEMO_REPLAY_URL)
      .then((loadedReplay) => {
        if (active) setReplay(loadedReplay);
      })
      .catch((loadError: unknown) => {
        if (active) setError(loadError instanceof Error ? loadError.message : String(loadError));
      });
    return () => {
      active = false;
    };
  }, []);

  const duration = replay ? replayDuration(replay.frames) : 0;

  useEffect(() => {
    if (!playing || duration <= 0) return;
    let animationFrame = 0;
    let previous = performance.now();

    const advance = (now: number) => {
      const elapsed = Math.min(0.1, (now - previous) / 1000);
      previous = now;
      setTime((current) => {
        const next = current + elapsed * speed;
        if (next >= duration) {
          setPlaying(false);
          return duration;
        }
        return next;
      });
      animationFrame = requestAnimationFrame(advance);
    };

    animationFrame = requestAnimationFrame(advance);
    return () => cancelAnimationFrame(animationFrame);
  }, [duration, playing, speed]);

  const frame = useMemo(() => (replay ? frameAtTime(replay.frames, time) : null), [replay, time]);
  const effects = useMemo(
    () => replay ? recentEvents(replay.events, time, replay.metadata.tick_rate_hz) : [],
    [replay, time],
  );
  const feedEvents = useMemo(() => {
    if (!replay || !frame) return [];
    return eventsThroughTick(filterFeedEvents(replay.events), frame.tick, 10);
  }, [frame, replay]);
  const selectedAgent = frame?.agents.find((agent) => agent.agent_id === selectedAgentId);

  const reset = () => {
    setPlaying(false);
    setTime(0);
  };

  if (error) {
    return <main className="status-screen"><h1>Replay unavailable</h1><p>{error}</p></main>;
  }

  if (!replay || !frame) {
    return <main className="status-screen"><div className="loader" /><p>Loading tactical replay...</p></main>;
  }

  const hasRanges = replay.frames.some((savedFrame) =>
    savedFrame.agents.some((agent) => typeof agent.attack_range === "number"),
  );
  const hasTargets = replay.frames.some((savedFrame) =>
    savedFrame.agents.some((agent) => agent.current_target_id != null),
  );

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CombatRL // replay command</p>
          <h1>3D Tactical Debrief</h1>
        </div>
        <div className="tick-card">
          <span>Simulation tick</span>
          <strong>{frame.tick.toString().padStart(4, "0")}</strong>
        </div>
      </header>

      <div className="workspace">
        <section className="viewer-card">
          <div className="viewer-toolbar">
            <div className="camera-tabs" aria-label="Camera mode">
              {(["angled", "top", "free"] as CameraMode[]).map((mode) => (
                <button
                  className={cameraMode === mode ? "active" : ""}
                  type="button"
                  key={mode}
                  onClick={() => setCameraMode(mode)}
                >
                  {mode === "top" ? "Top-down" : mode}
                </button>
              ))}
            </div>
            <div className="overlay-toggles">
              <label><input type="checkbox" checked={showRanges} disabled={!hasRanges} onChange={(event) => setShowRanges(event.target.checked)} /> ranges</label>
              <label><input type="checkbox" checked={showTargets} disabled={!hasTargets} onChange={(event) => setShowTargets(event.target.checked)} /> targets</label>
            </div>
          </div>
          <div className="canvas-wrap">
            <ArenaScene
              frame={frame}
              metadata={replay.metadata}
              events={effects}
              selectedAgentId={selectedAgentId}
              cameraMode={cameraMode}
              showRanges={showRanges && hasRanges}
              showTargets={showTargets && hasTargets}
              onSelectAgent={setSelectedAgentId}
            />
            <div className="arena-legend">
              <span><i className="team-dot team-dot-0" />Team 0</span>
              <span><i className="team-dot team-dot-1" />Team 1</span>
              <span>Drag to orbit · Wheel to zoom</span>
            </div>
          </div>
          <ReplayControls
            playing={playing}
            time={time}
            duration={duration}
            speed={speed}
            onToggle={() => setPlaying((value) => !value)}
            onReset={reset}
            onSeek={(nextTime) => {
              setPlaying(false);
              setTime(nextTime);
            }}
            onSpeed={setSpeed}
          />
        </section>

        <aside className="sidebar">
          <ReplayInfoPanel metadata={replay.metadata} summary={replay.summary} selectedAgent={selectedAgent} />
          <EventFeed events={feedEvents} />
          {(!hasRanges || !hasTargets || replay.events.length === 0) && (
            <section className="panel availability-note">
              <h2>Overlay availability</h2>
              {!hasRanges && <p>Attack ranges are absent from this replay.</p>}
              {!hasTargets && <p>Target links are absent from this replay.</p>}
              {replay.events.length === 0 && <p>The event stream is empty; effects and feed are disabled.</p>}
            </section>
          )}
        </aside>
      </div>
    </main>
  );
}
