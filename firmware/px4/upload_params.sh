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
if ! python3 - "$PORT" "$BAUD" << 'PYEOF'
import sys
port = sys.argv[1]
baud = int(sys.argv[2])
try:
    from pymavlink import mavutil
except ImportError:
    print('Error: pymavlink not installed. Run: pip install pymavlink', file=sys.stderr)
    sys.exit(1)
try:
    master = mavutil.mavlink_connection(port, baud=baud)
except PermissionError:
    print(f'Error: Permission denied on {port}. Try: sudo usermod -aG dialout $USER', file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error: Cannot open {port}: {e}', file=sys.stderr)
    sys.exit(1)
hb = master.wait_heartbeat(timeout=10)
if hb:
    print(f'Connected: autopilot type {hb.autopilot}, system {hb.get_srcSystem()}')
    master.close()
else:
    print('Error: No heartbeat received within 10 seconds', file=sys.stderr)
    sys.exit(1)
PYEOF
then
    echo ""
    echo "Could not connect to flight controller."
    echo "Check that:"
    echo "  1. Pixhawk is connected via USB (${PORT})"
    echo "  2. No other program (QGC, MAVProxy) is using the port"
    echo "  3. pymavlink is installed: pip install pymavlink"
    exit 1
fi
echo ""

TOTAL_SUCCESS=0
TOTAL_FAILED=0
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

    # Upload all parameters in a single MAVLink session via pymavlink
    # This avoids opening/closing the serial port per parameter
    RESULT=$(python3 - "$PORT" "$BAUD" "$filepath" << 'PYEOF'
import sys, re

port = sys.argv[1]
baud = int(sys.argv[2])
filepath = sys.argv[3]

from pymavlink import mavutil

master = mavutil.mavlink_connection(port, baud=baud)
master.wait_heartbeat(timeout=10)

success = 0
failed = 0

with open(filepath) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Parse "PARAM_NAME: value  # optional comment"
        match = re.match(r'^(\w+)\s*:\s*([^#]+)', line)
        if not match:
            continue
        param = match.group(1).strip()
        value_str = match.group(2).strip()
        try:
            value = float(value_str)
        except ValueError:
            print(f'  SKIP {param} (non-numeric: {value_str})')
            continue

        print(f'  SET {param} = {value}')
        master.param_set_send(param, value)
        ack = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
        if ack:
            print(f'    OK: {ack.param_id.rstrip(chr(0))} = {ack.param_value}')
            success += 1
        else:
            print(f'    TIMEOUT: {param}', file=sys.stderr)
            failed += 1

master.close()
# Print machine-readable counts on the last line
print(f'__COUNTS__ {success} {failed}')
PYEOF
    )

    echo "$RESULT" | grep -v '^__COUNTS__'

    # Extract counts from the Python output
    COUNTS=$(echo "$RESULT" | grep '^__COUNTS__' || echo "__COUNTS__ 0 0")
    FILE_SUCCESS=$(echo "$COUNTS" | awk '{print $2}')
    FILE_FAILED=$(echo "$COUNTS" | awk '{print $3}')
    TOTAL_SUCCESS=$((TOTAL_SUCCESS + FILE_SUCCESS))
    TOTAL_FAILED=$((TOTAL_FAILED + FILE_FAILED))
    echo ""
done

echo "=== Summary ==="
echo "  Set:     $TOTAL_SUCCESS"
echo "  Failed:  $TOTAL_FAILED"
echo "  Skipped: $SKIPPED files"

if [ "$TOTAL_FAILED" -gt 0 ]; then
    echo ""
    echo "WARNING: $TOTAL_FAILED parameter(s) failed to set."
    exit 1
fi

echo ""
echo "Done. Reboot the flight controller to apply all changes."
echo "  mavlink shell: reboot"
echo "  or: power cycle the Pixhawk"
