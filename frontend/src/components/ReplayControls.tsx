interface ReplayControlsProps {
  playing: boolean;
  time: number;
  duration: number;
  speed: number;
  onToggle: () => void;
  onReset: () => void;
  onSeek: (time: number) => void;
  onSpeed: (speed: number) => void;
}

const SPEEDS = [0.5, 1, 2, 4];

function formatTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds - minutes * 60;
  return `${minutes}:${remainder.toFixed(1).padStart(4, "0")}`;
}

export function ReplayControls({
  playing,
  time,
  duration,
  speed,
  onToggle,
  onReset,
  onSeek,
  onSpeed,
}: ReplayControlsProps) {
  return (
    <div className="replay-controls">
      <button className="primary-control" type="button" aria-keyshortcuts="Space" onClick={onToggle}>
        {playing ? "Pause" : "Play"}
      </button>
      <button type="button" aria-keyshortcuts="Home" onClick={onReset}>Reset</button>
      <span className="time-readout">{formatTime(time)} / {formatTime(duration)}</span>
      <input
        aria-label="Replay timeline"
        aria-describedby="replay-shortcuts"
        type="range"
        min={0}
        max={Math.max(duration, 0.01)}
        step={0.01}
        value={Math.min(time, duration)}
        onChange={(event) => onSeek(Number(event.target.value))}
      />
      <div className="speed-controls" aria-label="Playback speed">
        {SPEEDS.map((value) => (
          <button
            className={value === speed ? "active" : ""}
            type="button"
            key={value}
            aria-pressed={value === speed}
            onClick={() => onSpeed(value)}
          >
            {value}x
          </button>
        ))}
      </div>
      <span className="visually-hidden" id="replay-shortcuts">
        Shortcuts: Space play or pause, Home reset, arrows seek, 0 1 2 4 speed, C camera, F follow, R ranges, T targets.
      </span>
    </div>
  );
}
