#!/usr/bin/env bash
# Process a folder of geotagged images through OpenDroneMap (CLI)
# Usage: ./ground/odm/process.sh <image_folder> [profile]
#
# Outputs: orthophoto, DSM, 3D mesh, point cloud in <image_folder>/odm_output/

set -euo pipefail

IMAGE_DIR="${1:?Usage: process.sh <image_folder> [profile]}"
PROFILE="${2:-survey_standard}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_FILE="$SCRIPT_DIR/profiles/${PROFILE}.json"

if [ ! -d "$IMAGE_DIR" ]; then
    echo "Error: $IMAGE_DIR is not a directory"
    exit 1
fi

IMAGE_COUNT=$(ls -1 "$IMAGE_DIR"/*.jpg "$IMAGE_DIR"/*.JPG 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "Error: No images found in $IMAGE_DIR"
    echo "Expected .jpg or .JPG files. Check that images have been transferred."
    exit 1
fi
echo "Processing $IMAGE_COUNT images from $IMAGE_DIR"
echo "Profile: $PROFILE"

# Read ODM options from profile
ODM_OPTIONS=""
if [ -f "$PROFILE_FILE" ]; then
    # Parse JSON options into CLI flags
    ODM_OPTIONS=$(python3 -c "
import json, sys
with open('$PROFILE_FILE') as f:
    opts = json.load(f)
for k, v in opts.items():
    if isinstance(v, bool):
        if v: print(f'--{k}', end=' ')
    else:
        print(f'--{k} {v}', end=' ')
")
fi

echo "ODM options: $ODM_OPTIONS"
echo ""

# Run ODM via Docker
docker run -ti --rm \
    -v "$IMAGE_DIR":/datasets/project \
    opendronemap/odm \
    --project-path /datasets \
    $ODM_OPTIONS

echo ""
echo "=== Processing Complete ==="
echo "Outputs in: $IMAGE_DIR/odm_output/"
echo "  - odm_orthophoto/    Orthophoto (.tif)"
echo "  - odm_dem/           Digital Surface Model (.tif)"
echo "  - odm_texturing/     Textured 3D mesh (.obj)"
echo "  - odm_georeferencing/ Georeferenced point cloud (.laz)"
