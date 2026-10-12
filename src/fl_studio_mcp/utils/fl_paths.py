"""Path helpers for locating FL Studio settings across platforms.

Supports native macOS/Windows installs and Linux Wine/Bottles layouts.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path


def _native_settings_dir() -> Path:
    """Return the native FL Studio settings directory for this platform."""
    system = platform.system()

    if system in ("Darwin", "Windows"):
        return Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Settings"

    # Legacy Linux fallback for non-Wine users.
    return Path.home() / ".fl-studio" / "Settings"


def _bottles_roots() -> list[Path]:
    """Return candidate Bottles roots, honoring overrides."""
    roots: list[Path] = []

    explicit = os.environ.get("BOTTLES_DIR")
    if explicit:
        roots.append(Path(explicit).expanduser())

    roots.extend(
        [
            Path.home()
            / ".var"
            / "app"
            / "com.usebottles.bottles"
            / "data"
            / "bottles"
            / "bottles",
            Path.home() / ".local" / "share" / "bottles" / "bottles",
        ]
    )

    # Deduplicate while preserving order.
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            seen.add(key)
            deduped.append(root)
    return deduped


def _find_bottles_settings_dir() -> Path | None:
    """Locate FL Studio settings in Bottles and return the best match."""
    bottle_name = os.environ.get("FL_BOTTLE_NAME")
    wine_user_override = os.environ.get("FL_WINE_USER")

    for root in _bottles_roots():
        if not root.exists():
            continue

        bottle_dirs: list[Path]
        if bottle_name:
            bottle_dirs = [root / bottle_name]
        else:
            bottle_dirs = [p for p in root.iterdir() if p.is_dir()]

        for bottle_dir in bottle_dirs:
            users_root = bottle_dir / "drive_c" / "users"
            if not users_root.exists():
                continue

            user_dirs: list[Path] = []
            if wine_user_override:
                user_dirs.append(users_root / wine_user_override)

            # Prefer the host username first when present.
            host_user = os.environ.get("USER")
            if host_user:
                user_dirs.append(users_root / host_user)

            user_dirs.extend([p for p in users_root.iterdir() if p.is_dir()])

            # Deduplicate while preserving order.
            deduped_users: list[Path] = []
            seen_users: set[str] = set()
            for user_dir in user_dirs:
                key = str(user_dir)
                if key not in seen_users:
                    seen_users.add(key)
                    deduped_users.append(user_dir)

            for user_dir in deduped_users:
                settings = (
                    user_dir
                    / "Documents"
                    / "Image-Line"
                    / "FL Studio"
                    / "Settings"
                )
                if settings.exists():
                    return settings

    return None


def get_fl_settings_dir() -> Path:
    """Return the FL Studio settings directory for MCP integration.

    Search order:
    1. FL_STUDIO_SETTINGS_DIR env var (explicit override)
    2. Linux Bottles auto-detection (or FL_BOTTLE_NAME/FL_WINE_USER guided)
    3. Native platform default path
    """
    explicit = os.environ.get("FL_STUDIO_SETTINGS_DIR")
    if explicit:
        return Path(explicit).expanduser()

    if platform.system() == "Linux":
        settings = _find_bottles_settings_dir()
        if settings is not None:
            return settings

    return _native_settings_dir()


def get_fl_hardware_dir() -> Path:
    """Return the FL Studio Hardware scripts directory, creating it if needed."""
    hardware_dir = get_fl_settings_dir() / "Hardware" / "FLStudioMCP"
    hardware_dir.mkdir(parents=True, exist_ok=True)
    return hardware_dir


def get_fl_piano_scripts_dir() -> Path:
    """Return the FL Studio Piano roll scripts directory, creating it if needed."""
    scripts_dir = get_fl_settings_dir() / "Piano roll scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    return scripts_dir
