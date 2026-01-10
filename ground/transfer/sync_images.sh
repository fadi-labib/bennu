#!/usr/bin/env bash
# Sync captured images from Pi 5 to ground station
# Usage: ./ground/transfer/sync_images.sh [pi_host] [output_dir]
#
# Prerequisites:
#   - Pi 5 connected to same network (WiFi or USB ethernet)
#   - SSH key configured for passwordless access

set -euo pipefail

PI_HOST="${1:-pi@bennu.local}"
PI_CAPTURE_DIR="/home/pi/captures"
OUTPUT_DIR="${2:-$(pwd)/captures_$(date +%Y%m%d_%H%M%S)}"

echo "=== Syncing images from $PI_HOST ==="

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Count images on Pi
echo "Checking images on drone..."
IMAGE_COUNT=$(ssh "$PI_HOST" "ls -1 $PI_CAPTURE_DIR/*.jpg 2>/dev/null | wc -l")
echo "Found $IMAGE_COUNT images"

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "No images to transfer."
    exit 0
fi

# Transfer with rsync (resume-capable, shows progress)
rsync -avz --progress \
    "$PI_HOST:$PI_CAPTURE_DIR/*.jpg" \
    "$OUTPUT_DIR/"

echo ""
echo "=== Transfer Complete ==="
echo "Images saved to: $OUTPUT_DIR"
echo "Image count: $(ls -1 "$OUTPUT_DIR"/*.jpg | wc -l)"
echo ""
echo "Next step: Process with ODM"
echo "  ./ground/odm/process.sh $OUTPUT_DIR"
