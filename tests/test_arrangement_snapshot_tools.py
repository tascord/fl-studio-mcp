from __future__ import annotations

import fl_studio_mcp.utils.connection as connection
import fl_studio_mcp.tools.patterns_song as patterns_song


class DummyConn:
    def send_command(self, action, params=None, timeout=2.0):
        if action == "transport.getStatus":
            return {
                "success": True,
                "is_playing": True,
                "is_recording": False,
                "position": "00:00.000",
                "loop_mode": "song",
            }
        if action == "songLayout.get":
            return {
                "success": True,
                "mode": "song",
                "song_position": {"ticks": 480},
                "selection": {"start_tick": 0, "end_tick": 1920},
                "tracks": [{"index": 1, "name": "Drums"}],
                "markers": [{"index": 0, "name": "Verse"}],
            }
        if action == "patterns.list":
            return {
                "success": True,
                "active_pattern": 1,
                "patterns": [{"index": 1, "name": "Pattern 1"}],
            }
        if action == "mixer.getAllTracks":
            return {
                "success": True,
                "tracks": [{"index": 0, "name": "Master"}],
            }
        if action == "channels.getAll":
            return {
                "success": True,
                "channels": [{"index": 0, "name": "Kick"}],
            }
        return {"success": False, "error": f"Unexpected action: {action}"}


def test_snapshot_directory_rolls_out_for_custom_root(tmp_path):
    target = patterns_song._snapshot_directory(tmp_path / "custom-root")
    assert target == tmp_path / "custom-root" / ".fl_studio_mcp_snapshots"
    assert target.exists()


def test_collect_project_snapshot_wraps_current_state(monkeypatch):
    monkeypatch.setattr(connection, "get_connection", lambda: DummyConn())

    snapshot = patterns_song._collect_project_snapshot()

    assert snapshot["transport"]["is_playing"] is True
    assert snapshot["song_layout"]["tracks"][0]["name"] == "Drums"
    assert snapshot["patterns"]["active_pattern"] == 1
    assert snapshot["mixer_tracks"][0]["name"] == "Master"
