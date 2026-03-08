#!/usr/bin/env bash
# Upload PX4 parameters to Pixhawk 6C via MAVLink
# Usage: ./firmware/px4/upload_params.sh [param_file.yaml ...]
#
# If no files specified, uploads all param files in order.
#
# Prerequisites:
#   pip install pymavlink
#   Pixhawk connected via USB or telemetry radio

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMS_DIR="$SCRIPT_DIR/params"
PORT="${PX4_PORT:-/dev/ttyACM0}"
BAUD="${PX4_BAUD:-57600}"

# Validate params directory
if [ ! -d "$PARAMS_DIR" ]; then
    echo "Error: Parameters directory not found: $PARAMS_DIR"
    exit 1
fi

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

# Check that at least one param file exists
FOUND_FILES=0
for param_file in "${PARAM_FILES[@]}"; do
    filepath="$PARAMS_DIR/$param_file"
    [ -f "$filepath" ] || filepath="$param_file"
    [ -f "$filepath" ] && FOUND_FILES=$((FOUND_FILES + 1))
done

if [ "$FOUND_FILES" -eq 0 ]; then
    echo "Error: No parameter files found. Looked for:"
    for param_file in "${PARAM_FILES[@]}"; do
        echo "  - $PARAMS_DIR/$param_file"
    done
    exit 1
fi

# Validate MAVLink connection
echo "Connecting to flight controller at $PORT ($BAUD baud)..."
if ! python3 -c "
from pymavlink import mavutil
import sys
try:
    master = mavutil.mavlink_connection('$PORT', baud=$BAUD)
    hb = master.wait_heartbeat(timeout=10)
    if hb:
        print(f'Connected: autopilot type {hb.autopilot}, system {hb.get_srcSystem()}')
    else:
        print('Error: No heartbeat received within 10 seconds', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'Error: Cannot connect to {\"$PORT\"}: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1; then
    echo ""
    echo "Could not connect to flight controller."
    echo "Check that:"
    echo "  1. Pixhawk is connected via USB (${PORT})"
    echo "  2. No other program (QGC, MAVProxy) is using the port"
    echo "  3. pymavlink is installed: pip install pymavlink"
    exit 1
fi
echo ""

SUCCESS=0
FAILED=0
SKIPPED=0

for param_file in "${PARAM_FILES[@]}"; do
    filepath="$PARAMS_DIR/$param_file"
    if [ ! -f "$filepath" ]; then
        filepath="$param_file"  # Try as absolute/relative path
    fi

    if [ ! -f "$filepath" ]; then
        echo "SKIP: $param_file (not found)"
        SKIPPED=$((SKIPPED + 1))
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
            if python3 -c "
import sys
from pymavlink import mavutil
master = mavutil.mavlink_connection('$PORT', baud=$BAUD)
master.wait_heartbeat(timeout=10)
master.param_set_send('$param', float('$value'))
ack = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
if ack:
    print(f'    OK: {ack.param_id} = {ack.param_value}')
else:
    print(f'    TIMEOUT: $param', file=sys.stderr)
    sys.exit(1)
" 2>&1; then
                SUCCESS=$((SUCCESS + 1))
            else
                echo "    FAILED: $param"
                FAILED=$((FAILED + 1))
            fi
        fi
    done
    echo ""
done

echo "=== Summary ==="
echo "  Set:     $SUCCESS"
echo "  Failed:  $FAILED"
echo "  Skipped: $SKIPPED files"

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "WARNING: $FAILED parameter(s) failed to set."
    exit 1
fi

echo ""
echo "Done. Reboot the flight controller to apply all changes."
echo "  mavlink shell: reboot"
echo "  or: power cycle the Pixhawk"
