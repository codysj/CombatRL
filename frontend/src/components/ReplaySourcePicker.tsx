import { useEffect, useRef } from "react";

interface ReplaySourcePickerProps {
  label: string;
  loading: boolean;
  error: string | null;
  onFiles: (files: FileList) => void;
  onLoadDemo: () => void;
}

export function ReplaySourcePicker({
  label,
  loading,
  error,
  onFiles,
  onLoadDemo,
}: ReplaySourcePickerProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.setAttribute("webkitdirectory", "");
    inputRef.current?.setAttribute("directory", "");
  }, []);

  return (
    <div className="replay-source">
      <div className="source-label" aria-live="polite">
        <span>Replay source</span>
        <strong>{loading ? "Loading..." : label}</strong>
      </div>
      <div className="source-actions">
        <button type="button" disabled={loading} onClick={() => inputRef.current?.click()}>
          Open replay
        </button>
        <button type="button" disabled={loading} onClick={onLoadDemo}>
          Demo
        </button>
      </div>
      <input
        ref={inputRef}
        className="visually-hidden"
        type="file"
        multiple
        aria-label="Choose a CombatRL replay directory"
        onChange={(event) => {
          if (event.target.files?.length) onFiles(event.target.files);
          event.target.value = "";
        }}
      />
      {error && <p className="source-error" role="alert">{error}</p>}
    </div>
  );
}
