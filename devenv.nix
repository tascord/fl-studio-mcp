{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  packages = with pkgs; [
    git
    uv
    python312
    python312Packages.pip
    xdotool
    alsa-lib
    alsa-utils
    jack2
    ripgrep
    jq
  ];

  env.PYTHONUNBUFFERED = "1";
  env.LD_LIBRARY_PATH = lib.makeLibraryPath [ pkgs.alsa-lib ];

  scripts.fl-mcp-sync.exec = ''
    set -e
    uv python install 3.12
    uv sync --python 3.12
  '';
  scripts.fl-mcp-sync.description = "Install project dependencies with uv (Python 3.12)";

  scripts.fl-mcp-run.exec = ''
    set -e
    exec uv run --python 3.12 fl-studio-mcp
  '';
  scripts.fl-mcp-run.description = "Run FL Studio MCP server";

  scripts.fl-mcp-setup.exec = ''
    set -e
    exec bash scripts/setup.sh
  '';
  scripts.fl-mcp-setup.description = "Install FL scripts into native or Wine/Bottles FL Studio Settings";

  scripts.fl-mcp-doctor.exec = ''
    set -e
    uv run --python 3.12 python - <<'PY'
from fl_studio_mcp.utils.fl_paths import get_fl_settings_dir
from fl_studio_mcp.utils.connection import get_connection

print("FL settings:", get_fl_settings_dir())
status = get_connection().get_status()
print("Connected:", status.get("connected"))
print("Selected port:", status.get("port_name"))
print("Hardware dir:", status.get("hardware_dir"))
print("Command file:", status.get("command_file"))
print("Available ports:")
for p in status.get("available_ports", []):
    print(" -", p)
if status.get("error"):
    print("Error:", status.get("error"))
PY
  '';
  scripts.fl-mcp-doctor.description = "Show resolved FL path and MIDI port visibility diagnostics";

  enterShell = ''
    echo "-- fl-studio-mcp devenv --"
    python --version 2>/dev/null | sed 's/^/python /' || true
    uv --version 2>/dev/null | sed 's/^/uv /' || true
    echo ""
    echo "First run:"
    echo "  fl-mcp-sync"
    echo "  fl-mcp-setup"
    echo "  fl-mcp-doctor"
    echo "  fl-mcp-run"
    echo ""
    echo "Optional Linux Wine/Bottles overrides:"
    echo "  FL_STUDIO_SETTINGS_DIR=/path/to/.../FL Studio/Settings"
    echo "  FL_BOTTLE_NAME=<bottle-name>"
    echo "  FL_WINE_USER=<wine-user>"
  '';
}
