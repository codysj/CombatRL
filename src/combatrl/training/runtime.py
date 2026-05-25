"""Runtime setup for headless training imports."""

import os
from pathlib import Path


def configure_training_runtime() -> None:
    """Keep optional plotting caches inside the repo during headless SB3 runs."""
    matplotlib_dir = Path("artifacts/reports/matplotlib")
    matplotlib_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_dir))
