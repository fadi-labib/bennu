# Transfer Images from Drone

Sync captured images from the Raspberry Pi 4 on the drone to your ground
station workstation. The transfer uses `rsync` so it is resume-capable -- if the
connection drops, re-run the command to pick up where it left off.

!!! abstract "Prerequisites"

    - Raspberry Pi 4 powered on and connected to the same WiFi network as your workstation
    - SSH key configured for passwordless access to the Pi (`ssh-copy-id pi@bennu.local`)

## Usage

### Default (recommended)

```bash
./ground/transfer/sync_images.sh
```

Connects to `pi@bennu.local` and saves images to a timestamped folder in the
current directory (e.g., `./captures_20260308_143022/`).

### Custom Host

```bash
./ground/transfer/sync_images.sh pi@192.168.1.50
```

### Custom Host and Output Directory

```bash
./ground/transfer/sync_images.sh pi@192.168.1.50 ~/drone_images/flight_003
```

## What Happens

1. The script connects to the Pi via SSH and counts images in `/home/pi/captures`
2. If images are found, `rsync` transfers all `.jpg` files with progress display
3. A summary prints the local output path and total image count

```
=== Syncing images from pi@bennu.local ===
Checking images on drone...
Found 247 images
...
=== Transfer Complete ===
Images saved to: ./captures_20260308_143022
Image count: 247
```

## Next Step

Process the transferred images with OpenDroneMap:

```bash
./ground/odm/process.sh ./captures_20260308_143022
```

See [Start WebODM and Process Images](start-webodm.md) for the full processing
workflow.
