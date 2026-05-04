from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogPaths:
    root: Path
    gui_sessions: Path
    one_shot: Path
    continuous: Path
    errors: Path
    index: Path
    events: Path


def build_log_paths(root_dir: str | Path) -> LogPaths:
    root = Path(root_dir)
    paths = LogPaths(
        root=root,
        gui_sessions=root / "gui_sessions",
        one_shot=root / "one_shot",
        continuous=root / "continuous",
        errors=root / "errors",
        index=root / "index",
        events=root / "events",
    )
    for path in paths.__dict__.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
