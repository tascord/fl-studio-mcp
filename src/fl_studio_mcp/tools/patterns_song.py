"""Pattern and Song layout tools for FL Studio."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def _snapshot_directory(root: str | Path | None = None) -> Path:
    """Return the root directory used for FL Studio project snapshots."""
    base = Path(root) if root is not None else Path.cwd()
    if base.name == ".fl_studio_mcp_snapshots":
        target = base
    else:
        target = base / ".fl_studio_mcp_snapshots"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _collect_project_snapshot() -> dict:
    """Gather a compact project summary suitable for snapshotting."""
    from fl_studio_mcp.utils.connection import get_connection

    conn = get_connection()
    transport = conn.send_command("transport.getStatus")
    song_layout = conn.send_command("songLayout.get", {
        "include_tracks": True,
        "include_markers": True,
        "max_markers": 256,
    })
    patterns = conn.send_command("patterns.list", {"max_results": 128})
    mixer_tracks = conn.send_command("mixer.getAllTracks", {"include_empty": True})
    channels = conn.send_command("channels.getAll")

    def _normalize(response: dict) -> dict:
        if not response.get("success", False):
            return {"error": response.get("error")}
        payload = dict(response)
        payload.pop("success", None)
        return payload

    snapshot = {
        "version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "transport": _normalize(transport),
        "song_layout": _normalize(song_layout),
        "patterns": _normalize(patterns),
        "mixer_tracks": _normalize(mixer_tracks).get("tracks", []),
        "channels": _normalize(channels).get("channels", []),
    }
    return snapshot


def _read_snapshot_file(name: str, root: str | Path | None = None) -> Path:
    """Resolve a snapshot by name and return its path."""
    snapshot_name = str(name).strip()
    if not snapshot_name:
        raise ValueError("Snapshot name is required")

    file_path = _snapshot_directory(root) / f"{snapshot_name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_name}")
    return file_path


def register_pattern_song_tools(mcp: FastMCP) -> None:
    """Register pattern and song layout tools with the MCP server."""
    from fl_studio_mcp.utils.connection import get_connection

    @mcp.tool()
    def fl_create_pattern(name: str = "", index: int | None = None) -> dict:
        """Create a new pattern (or at a specific index) and activate it.

        Args:
            name: Optional pattern name. If empty, FL keeps default naming.
            index: Optional 1-based pattern index. If omitted, uses next slot.
        """
        conn = get_connection()
        payload = {"name": name}
        if index is not None:
            payload["index"] = index

        result = conn.send_command("patterns.create", payload)
        if not result.get("success", False) and "error" in result:
            return {"error": result["error"]}

        return {
            "index": result.get("index"),
            "name": result.get("name"),
            "active": result.get("active", False),
            "created": result.get("created", False),
        }

    @mcp.tool()
    def fl_switch_pattern(index: int, preview: bool = False) -> str:
        """Switch the active pattern.

        Args:
            index: 1-based pattern index
            preview: If True, ask FL to preview playback when switching.
        """
        conn = get_connection()
        result = conn.send_command("patterns.switch", {
            "index": index,
            "preview": preview,
        })

        if not result.get("success", False) and "error" in result:
            return f"Error: {result['error']}"

        name = result.get("name", f"Pattern {index}")
        return f"Active pattern is now {index} ('{name}')"

    @mcp.tool()
    def fl_get_current_pattern() -> dict:
        """Get details about the currently active pattern."""
        conn = get_connection()
        result = conn.send_command("patterns.getCurrent")

        if not result.get("success", False) and "error" in result:
            return {"error": result["error"]}

        return {
            "index": result.get("index"),
            "name": result.get("name"),
            "length_beats": result.get("length_beats"),
            "is_selected": result.get("is_selected", False),
            "is_default": result.get("is_default", False),
        }

    @mcp.tool()
    def fl_list_patterns(max_results: int = 128) -> dict:
        """List known patterns and basic metadata.

        Args:
            max_results: Maximum number of patterns to return.
        """
        conn = get_connection()
        result = conn.send_command("patterns.list", {"max_results": max_results})

        if not result.get("success", False) and "error" in result:
            return {"error": result["error"]}

        return {
            "active_pattern": result.get("active_pattern"),
            "count": result.get("count", 0),
            "patterns": result.get("patterns", []),
        }

    @mcp.tool()
    def fl_place_song_marker(name: str, tick: int | None = None) -> str:
        """Place a named marker in the Song layout (Playlist arrangement).

        Args:
            name: Marker label.
            tick: Absolute tick position. If omitted, uses current song position.
        """
        payload = {"name": name}
        if tick is not None:
            payload["tick"] = tick

        conn = get_connection()
        result = conn.send_command("songLayout.placeMarker", payload)

        if not result.get("success", False) and "error" in result:
            return f"Error: {result['error']}"

        placed_tick = result.get("tick")
        return f"Placed marker '{name}' at tick {placed_tick}."

    @mcp.tool()
    def fl_get_song_layout(
        include_tracks: bool = True,
        include_markers: bool = True,
        max_markers: int = 256,
    ) -> dict:
        """Query the Song layout state.

        Returns:
            - current mode and song position
            - arrangement selection bounds
            - playlist track states (optional)
            - arrangement markers (optional)
        """
        conn = get_connection()
        result = conn.send_command("songLayout.get", {
            "include_tracks": include_tracks,
            "include_markers": include_markers,
            "max_markers": max_markers,
        })

        if not result.get("success", False) and "error" in result:
            return {"error": result["error"]}

        return {
            "mode": result.get("mode"),
            "song_position": result.get("song_position", {}),
            "selection": result.get("selection", {}),
            "tracks": result.get("tracks", []),
            "markers": result.get("markers", []),
        }

    @mcp.tool()
    def fl_get_arrangement_overview() -> dict:
        """Return a compact arrangement overview with transport, song layout, and pattern state."""
        conn = get_connection()
        transport = conn.send_command("transport.getStatus")
        song_layout = conn.send_command("songLayout.get", {
            "include_tracks": True,
            "include_markers": True,
            "max_markers": 256,
        })
        patterns = conn.send_command("patterns.list", {"max_results": 128})

        if transport.get("success") is False and "error" in transport:
            return {"error": transport["error"]}
        if song_layout.get("success") is False and "error" in song_layout:
            return {"error": song_layout["error"]}
        if patterns.get("success") is False and "error" in patterns:
            return {"error": patterns["error"]}

        return {
            "transport": {
                "is_playing": transport.get("is_playing", False),
                "is_recording": transport.get("is_recording", False),
                "position": transport.get("position", ""),
                "loop_mode": transport.get("loop_mode", "pattern"),
            },
            "song_layout": {
                "mode": song_layout.get("mode"),
                "song_position": song_layout.get("song_position", {}),
                "selection": song_layout.get("selection", {}),
                "marker_count": len(song_layout.get("markers", [])),
                "track_count": len(song_layout.get("tracks", [])),
                "markers": song_layout.get("markers", []),
            },
            "patterns": {
                "active_pattern": patterns.get("active_pattern"),
                "count": patterns.get("count", 0),
                "patterns": patterns.get("patterns", []),
            },
        }

    @mcp.tool()
    def fl_get_automation_summary() -> dict:
        """Return a compact summary of automation-relevant state.

        This intentionally keeps the output small and safe: the FL scripting API in this
        project exposes arrangement, pattern, and parameter state more reliably than raw
        automation-lane operations, so this summary helps AI workflows reason about the
        current project without requiring unsupported deep automation APIs.
        """
        conn = get_connection()
        song_layout = conn.send_command("songLayout.get", {
            "include_tracks": True,
            "include_markers": True,
            "max_markers": 256,
        })
        mixer_tracks = conn.send_command("mixer.getAllTracks", {"include_empty": True})
        channels = conn.send_command("channels.getAll")

        if song_layout.get("success") is False and "error" in song_layout:
            return {"error": song_layout["error"]}
        if mixer_tracks.get("success") is False and "error" in mixer_tracks:
            return {"error": mixer_tracks["error"]}
        if channels.get("success") is False and "error" in channels:
            return {"error": channels["error"]}

        channel_count = len(channels.get("channels", []))
        track_count = len(mixer_tracks.get("tracks", []))
        return {
            "automation_status": "limited",
            "notes": "FL automation lane APIs are not uniformly exposed through the current FL Studio scripting layer; this summary focuses on arrangement, mixer, and channel state that influences automation decisions.",
            "song_layout": song_layout.get("selection", {}),
            "channel_count": channel_count,
            "mixer_track_count": track_count,
            "mixer_tracks": mixer_tracks.get("tracks", [])[:12],
            "channels": channels.get("channels", [])[:12],
        }

    @mcp.tool()
    def fl_list_project_snapshots(root: str | None = None) -> list[dict]:
        """List saved FL Studio project snapshots in a specific root directory."""
        snapshots_dir = _snapshot_directory(root)
        entries: list[dict] = []
        for snapshot_file in sorted(snapshots_dir.glob("*.json")):
            try:
                payload = json.loads(snapshot_file.read_text())
            except json.JSONDecodeError:
                payload = {"version": 0}

            entries.append({
                "name": snapshot_file.stem,
                "path": str(snapshot_file),
                "updated_at": snapshot_file.stat().st_mtime,
                "timestamp_utc": payload.get("timestamp_utc"),
            })
        return entries

    @mcp.tool()
    def fl_save_project_snapshot(name: str, root: str | None = None) -> dict:
        """Save a compact project snapshot to disk for later comparison or restore."""
        snapshot_name = (name or "snapshot").strip() or "snapshot"
        snapshot_dir = _snapshot_directory(root)
        payload = _collect_project_snapshot()
        path = snapshot_dir / f"{snapshot_name}.json"
        path.write_text(json.dumps(payload, indent=2))
        return {
            "saved": True,
            "name": snapshot_name,
            "path": str(path),
            "timestamp_utc": payload.get("timestamp_utc"),
        }

    @mcp.tool()
    def fl_restore_project_snapshot(name: str, root: str | None = None) -> dict:
        """Load a saved project snapshot and return its metadata.

        This does not blindly reapply all FL Studio state because the scripting API in this
        project does not expose a complete project-restore primitive. It is best used as a
        project-state reference and a safer way to compare before/after arrangements.
        """
        snapshot_name = str(name).strip()
        if not snapshot_name:
            return {"error": "Snapshot name is required"}

        try:
            path = _read_snapshot_file(snapshot_name, root)
            payload = json.loads(path.read_text())
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}

        return {
            "restored": True,
            "name": snapshot_name,
            "path": str(path),
            "timestamp_utc": payload.get("timestamp_utc"),
            "transport": payload.get("transport", {}),
            "song_layout": payload.get("song_layout", {}),
            "patterns": payload.get("patterns", {}),
        }
