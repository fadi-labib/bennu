#!/usr/bin/env bash
# Flash PX4 firmware to Holybro Pixhawk 6C
# Usage: ./firmware/px4/flash.sh [firmware_file.px4]
#
# If no firmware file provided, downloads the latest stable release
# for the holybro_pixhawk6c target.
#
# Prerequisites:
#   pip install pyserial
#   PX4-Autopilot repo cloned (for px_uploader.py) OR use QGroundControl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
BOARD="holybro_pixhawk6c"

# Read target version
PX4_VERSION=$(grep PX4_VERSION "$VERSION_FILE" | cut -d= -f2)

FIRMWARE_FILE="${1:-}"

if [ -z "$FIRMWARE_FILE" ]; then
    echo "Downloading PX4 $PX4_VERSION for $BOARD..."
    FIRMWARE_FILE="/tmp/px4_${BOARD}_${PX4_VERSION}.px4"
    curl -L -o "$FIRMWARE_FILE" \
        "https://github.com/PX4/PX4-Autopilot/releases/download/${PX4_VERSION}/${BOARD}.px4"
    echo "Downloaded to $FIRMWARE_FILE"
fi

echo ""
echo "=== Flash Instructions ==="
echo ""
echo "Option A: QGroundControl (recommended for first-time)"
echo "  1. Open QGroundControl"
echo "  2. Go to Vehicle Setup > Firmware"
echo "  3. Connect Pixhawk via USB"
echo "  4. Select PX4 Flight Stack > $PX4_VERSION"
echo "  5. Wait for flash to complete"
echo ""
echo "Option B: Command line (px_uploader.py)"
echo "  1. Connect Pixhawk via USB"
echo "  2. Run: python3 px_uploader.py --port /dev/ttyACM0 $FIRMWARE_FILE"
echo ""
echo "After flashing, update $VERSION_FILE with the flash date."
