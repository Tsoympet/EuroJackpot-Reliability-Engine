"""Shared package-root, user-data, and version helpers."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def package_root() -> Path:
    """Directory containing bundled read-only project assets."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def read_version(root: Path | None = None) -> str:
    """Return the project version from VERSION (fallback 3.8.0)."""
    path = (root or package_root()) / "VERSION"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "3.8.0"
    return value or "3.8.0"


def short_version(version: str | None = None) -> str:
    """Major.minor display form (e.g. 3.8.0 -> 3.8)."""
    value = version or read_version()
    parts = value.split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return value


def user_data_dir() -> Path:
    """
    Writable per-user data directory.

    Override with EUROJACKPOT_DATA_DIR for CI, packaging tests, or portable runs.
    """
    override = os.environ.get("EUROJACKPOT_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "EuroJackpotEngine"
    xdg = os.environ.get("XDG_DATA_HOME")
    return (Path(xdg) if xdg else Path.home() / ".local" / "share") / "eurojackpot-engine"


def ensure_user_layout(
    bundled_db: Path | None = None,
    *,
    db_name: str = "EuroJackpot_Operational_v3_8.sqlite",
) -> dict[str, Path]:
    """Create the user-data tree and seed the operational DB once."""
    data = user_data_dir()
    outputs = data / "outputs"
    logs = data / "logs"
    engine_out = data / "engine"
    data.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    engine_out.mkdir(parents=True, exist_ok=True)

    db_path = data / db_name
    if not db_path.exists() and bundled_db is not None and bundled_db.exists():
        shutil.copy2(bundled_db, db_path)
    elif not db_path.exists():
        db_path.touch()

    return {
        "data": data,
        "outputs": outputs,
        "logs": logs,
        "engine": engine_out,
        "db": db_path,
    }
