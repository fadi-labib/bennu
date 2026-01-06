#!/usr/bin/env bash
# Upload PX4 parameters to Pixhawk 6C via MAVLink
# Usage: ./firmware/px4/upload_params.sh [param_file.yaml ...]
#
# If no files specified, uploads all param files in order.
#
# Prerequisites:
#   pip install pymavlink mavsdk
#   Pixhawk connected via USB or telemetry radio

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMS_DIR="$SCRIPT_DIR/params"
PORT="${PX4_PORT:-/dev/ttyACM0}"
BAUD="${PX4_BAUD:-57600}"

# Ordered list of param files (apply in this order)
PARAM_FILES=(
    "base_params.yaml"
    "motor_params.yaml"
    "gps_params.yaml"
    "companion_params.yaml"
    "camera_params.yaml"
    "tuning_params.yaml"
)

# If specific files provided, use those instead
if [ $# -gt 0 ]; then
    PARAM_FILES=("$@")
fi

echo "Uploading PX4 parameters via $PORT at $BAUD baud"
echo ""

for param_file in "${PARAM_FILES[@]}"; do
    filepath="$PARAMS_DIR/$param_file"
    if [ ! -f "$filepath" ]; then
        filepath="$param_file"  # Try as absolute/relative path
    fi

    if [ ! -f "$filepath" ]; then
        echo "WARNING: $param_file not found, skipping"
        continue
    fi

    echo "--- Applying: $param_file ---"

    # Parse YAML and set each parameter via mavlink shell
    # Format: PARAM_NAME: value  or  PARAM_NAME: value  # comment
    grep -v '^#' "$filepath" | grep -v '^$' | while IFS=': ' read -r param value rest; do
        # Strip trailing comments
        value=$(echo "$value" | sed 's/#.*//' | xargs)
        if [ -n "$param" ] && [ -n "$value" ]; then
            echo "  SET $param = $value"
            # Using mavlink shell via pymavlink
            python3 -c "
import sys
from pymavlink import mavutil
master = mavutil.mavlink_connection('$PORT', baud=$BAUD)
master.wait_heartbeat()
master.param_set_send('$param', float('$value'))
ack = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
if ack:
    print(f'    OK: {ack.param_id} = {ack.param_value}')
else:
    print(f'    TIMEOUT: $param', file=sys.stderr)
" 2>&1 || echo "    FAILED: $param"
        fi
    done
    echo ""
done

echo "Done. Reboot the flight controller to apply all changes."
echo "  mavlink shell: reboot"
echo "  or: power cycle the Pixhawk"
