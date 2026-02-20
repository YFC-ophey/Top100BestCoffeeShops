from __future__ import annotations

import os
from pathlib import Path


def load_env_file(base_dir: Path, filename: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a local .env file.

    Existing environment variables are preserved.
    """
    candidates: list[Path] = [base_dir / filename]
    # When running inside a git worktree, prefer local .env first but allow root fallback.
    if base_dir.parent.name == ".worktrees":
        candidates.append(base_dir.parent.parent / filename)

    for env_path in candidates:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
