#!/usr/bin/env bash
# Auto-download and launch QGroundControl for the Bennu ground station.
#
# On first run, downloads the official AppImage to ~/.local/share/bennu/.
# On subsequent runs, launches the cached AppImage. Skips silently if no
# display is available (CI runners, SSH sessions without X forwarding).
#
# QGC auto-connects to PX4 on UDP 14550 — no extra config needed.

set -euo pipefail

QGC_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bennu"
QGC_APP="${QGC_DIR}/QGroundControl-x86_64.AppImage"
QGC_URL="https://d176tv9ibo4jno.cloudfront.net/latest/QGroundControl-x86_64.AppImage"

# No display → skip (CI, headless SSH, etc.)
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "[qgc] No display detected (\$DISPLAY and \$WAYLAND_DISPLAY both unset). Skipping launch."
    exit 0
fi

# Already running → don't double-launch
if pgrep -f "QGroundControl-x86_64.AppImage" >/dev/null 2>&1; then
    echo "[qgc] QGroundControl already running."
    exit 0
fi

# First-time download
if [ ! -x "$QGC_APP" ]; then
    echo "[qgc] First run — downloading QGroundControl AppImage (~80 MB)..."
    mkdir -p "$QGC_DIR"
    if ! curl -fL --progress-bar "$QGC_URL" -o "$QGC_APP"; then
        echo "[qgc] ERROR: download failed. Check connectivity or download manually:" >&2
        echo "[qgc]   $QGC_URL -> $QGC_APP" >&2
        exit 1
    fi
    chmod +x "$QGC_APP"
    echo "[qgc] Installed to $QGC_APP"
fi

# Launch detached. --appimage-extract-and-run avoids the libfuse2 dependency
# that Ubuntu 24.04 doesn't install by default.
echo "[qgc] Launching QGroundControl (auto-connects to PX4 on UDP 14550)..."
nohup "$QGC_APP" --appimage-extract-and-run >/dev/null 2>&1 &
disown
