import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { EventFeed, filterFeedEvents } from "./components/EventFeed";
import { ReplayControls } from "./components/ReplayControls";
import { ReplayInfoPanel } from "./components/ReplayInfoPanel";
import { ReplaySourcePicker } from "./components/ReplaySourcePicker";
import { frameAtTime } from "./replay/interpolate";
import { isEditableTarget, replayShortcutForKey } from "./replay/keyboard";
import { loadReplay, loadReplayFiles } from "./replay/loadReplay";
import { eventsThroughTick, recentEvents, replayDuration } from "./replay/replayTimeline";
import type { ReplayBundle } from "./replay/types";
import type { CameraMode } from "./render3d/ArenaScene";

const ArenaScene = lazy(() => import("./render3d/ArenaScene").then((module) => ({
  default: module.ArenaScene,
})));
const DEMO_REPLAY_URL = "/demo-replays/close-2v2";
const CAMERA_MODES: CameraMode[] = ["angled", "top", "free"];

export default function App() {
  const [replay, setReplay] = useState<ReplayBundle | null>(null);
  const [sourceLabel, setSourceLabel] = useState("Bundled close-2v2 demo");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [cameraMode, setCameraMode] = useState<CameraMode>("angled");
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [followSelected, setFollowSelected] = useState(false);
  const [showRanges, setShowRanges] = useState(true);
  const [showTargets, setShowTargets] = useState(true);

  const applyReplay = useCallback((nextReplay: ReplayBundle, label: string) => {
    setReplay(nextReplay);
    setSourceLabel(label);
    setPlaying(false);
    setTime(0);
    setSelectedAgentId(null);
    setFollowSelected(false);
    setLoadError(null);
  }, []);

  const loadDemo = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      applyReplay(await loadReplay(DEMO_REPLAY_URL), "Bundled close-2v2 demo");
    } catch (error: unknown) {
      setLoadError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }, [applyReplay]);

  useEffect(() => {
    void loadDemo();
  }, [loadDemo]);

  const loadLocalFiles = useCallback(async (files: FileList) => {
    setLoading(true);
    setLoadError(null);
    try {
      const loaded = await loadReplayFiles(files);
      applyReplay(loaded.replay, loaded.label);
    } catch (error: unknown) {
      setLoadError(error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }, [applyReplay]);

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

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isEditableTarget(event.target) || event.altKey || event.ctrlKey || event.metaKey) return;
      const shortcut = replayShortcutForKey(event.key);
      if (!shortcut) return;
      event.preventDefault();
      switch (shortcut.type) {
        case "toggle_play":
          setPlaying((value) => !value);
          break;
        case "reset":
          setPlaying(false);
          setTime(0);
          break;
        case "seek_relative":
          setPlaying(false);
          setTime((value) => Math.max(0, Math.min(duration, value + shortcut.seconds)));
          break;
        case "set_speed":
          setSpeed(shortcut.speed);
          break;
        case "cycle_camera":
          setCameraMode((value) => CAMERA_MODES[(CAMERA_MODES.indexOf(value) + 1) % CAMERA_MODES.length]);
          break;
        case "toggle_follow":
          if (selectedAgentId) setFollowSelected((value) => !value);
          break;
        case "toggle_ranges":
          setShowRanges((value) => !value);
          break;
        case "toggle_targets":
          setShowTargets((value) => !value);
          break;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [duration, selectedAgentId]);

  const frame = useMemo(() => replay ? frameAtTime(replay.frames, time) : null, [replay, time]);
  const effects = useMemo(
    () => replay ? recentEvents(replay.events, time, replay.metadata.tick_rate_hz) : [],
    [replay, time],
  );
  const feedEvents = useMemo(() => {
    if (!replay || !frame) return [];
    return eventsThroughTick(filterFeedEvents(replay.events), frame.tick, 10);
  }, [frame, replay]);
  const selectedAgent = frame?.agents.find((agent) => agent.agent_id === selectedAgentId);

  const sourcePicker = (
    <ReplaySourcePicker
      label={sourceLabel}
      loading={loading}
      error={loadError}
      onFiles={(files) => void loadLocalFiles(files)}
      onLoadDemo={() => void loadDemo()}
    />
  );

  if (!replay || !frame) {
    return (
      <main className="status-screen">
        {loading && <div className="loader" />}
        <h1>{loadError ? "Replay unavailable" : "Loading tactical replay"}</h1>
        {sourcePicker}
      </main>
    );
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
        {sourcePicker}
        <div className="tick-card">
          <span>Simulation tick</span>
          <strong>{frame.tick.toString().padStart(4, "0")}</strong>
        </div>
      </header>

      <div className="workspace">
        <section className="viewer-card" aria-label="Replay viewer">
          <div className="viewer-toolbar">
            <div className="camera-tabs" aria-label="Camera mode">
              {CAMERA_MODES.map((mode) => (
                <button
                  className={cameraMode === mode ? "active" : ""}
                  type="button"
                  key={mode}
                  aria-pressed={cameraMode === mode}
                  aria-keyshortcuts="C"
                  onClick={() => setCameraMode(mode)}
                >
                  {mode === "top" ? "Top-down" : mode}
                </button>
              ))}
              <button
                type="button"
                className={followSelected ? "active" : ""}
                aria-pressed={followSelected}
                aria-keyshortcuts="F"
                disabled={!selectedAgentId}
                title={selectedAgentId ? "Follow selected agent (F)" : "Select an agent to enable follow mode"}
                onClick={() => setFollowSelected((value) => !value)}
              >
                Follow
              </button>
            </div>
            <div className="overlay-toggles">
              <label><input type="checkbox" checked={showRanges} disabled={!hasRanges} onChange={(event) => setShowRanges(event.target.checked)} /> ranges</label>
              <label><input type="checkbox" checked={showTargets} disabled={!hasTargets} onChange={(event) => setShowTargets(event.target.checked)} /> targets</label>
            </div>
          </div>
          <div className="canvas-wrap">
            <Suspense fallback={<div className="scene-loading"><div className="loader" />Loading 3D renderer...</div>}>
              <ArenaScene
                frame={frame}
                metadata={replay.metadata}
                events={effects}
                selectedAgentId={selectedAgentId}
                followSelected={followSelected}
                cameraMode={cameraMode}
                showRanges={showRanges && hasRanges}
                showTargets={showTargets && hasTargets}
                onSelectAgent={(agentId) => {
                  setSelectedAgentId(agentId);
                  if (!agentId) setFollowSelected(false);
                }}
              />
            </Suspense>
            <div className="arena-legend">
              <span><i className="team-dot team-dot-0" />Team 0</span>
              <span><i className="team-dot team-dot-1" />Team 1</span>
              <span>Drag to orbit · Wheel to zoom · Space to pause</span>
            </div>
          </div>
          <ReplayControls
            playing={playing}
            time={time}
            duration={duration}
            speed={speed}
            onToggle={() => setPlaying((value) => !value)}
            onReset={() => { setPlaying(false); setTime(0); }}
            onSeek={(nextTime) => { setPlaying(false); setTime(nextTime); }}
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
          <section className="panel shortcut-panel">
            <h2>Keyboard</h2>
            <p><kbd>Space</kbd> play · <kbd>←</kbd><kbd>→</kbd> seek · <kbd>C</kbd> camera · <kbd>F</kbd> follow</p>
          </section>
        </aside>
      </div>
    </main>
  );
}
