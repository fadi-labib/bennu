# Flash PX4 Firmware and Parameters

Flash the PX4 firmware onto the Holybro Pixhawk 6C and upload Bennu's tuned
parameter files. This guide covers both the initial firmware flash and the
parameter upload workflow.

!!! abstract "Prerequisites"

    - [QGroundControl](https://docs.qgroundcontrol.com/master/en/qgc-user-guide/getting_started/download_and_install.html) installed
    - Python dependencies installed: `pip install pyserial pymavlink mavsdk`
    - Pixhawk 6C connected to your computer via USB

## Flash Firmware

The `firmware/px4/flash.sh` script downloads the correct PX4 firmware for the
Pixhawk 6C. Run it from the repo root:

```bash
./firmware/px4/flash.sh
```

To flash a firmware file you already have:

```bash
./firmware/px4/flash.sh path/to/firmware.px4
```

After the script downloads the firmware, choose one of the two methods below.

### Option A: QGroundControl (recommended)

1. Open QGroundControl
2. Go to **Vehicle Setup > Firmware**
3. Connect the Pixhawk via USB
4. Select **PX4 Flight Stack** and the matching version
5. Wait for the flash to complete

### Option B: Command Line

1. Connect the Pixhawk via USB
2. Run:

    ```bash
    python3 px_uploader.py --port /dev/ttyACM0 /tmp/px4_holybro_pixhawk6c_<version>.px4
    ```

    This requires `px_uploader.py` from the PX4-Autopilot source tree.

## Upload Parameters

The `firmware/px4/upload_params.sh` script applies Bennu's parameter files to
the flight controller via MAVLink.

### Upload All Parameters (default)

```bash
./firmware/px4/upload_params.sh
```

This applies all 6 parameter files in the correct order.

### Upload Specific Files

```bash
./firmware/px4/upload_params.sh camera_params.yaml tuning_params.yaml
```

### Environment Variables

| Variable   | Default         | Description              |
|------------|-----------------|--------------------------|
| `PX4_PORT` | `/dev/ttyACM0`  | Serial port to Pixhawk   |
| `PX4_BAUD` | `57600`         | Baud rate for MAVLink     |

Example with a custom port:

```bash
PX4_PORT=/dev/ttyUSB0 ./firmware/px4/upload_params.sh
```

After uploading, **reboot the flight controller** to apply changes (power cycle
the Pixhawk or send `reboot` via the MAVLink shell).

## Parameter Files

The script applies these files in order from `firmware/px4/params/`:

| File                    | Configures                                 |
|-------------------------|--------------------------------------------|
| `base_params.yaml`      | Frame type, EKF2, failsafes, battery       |
| `motor_params.yaml`     | DShot600 protocol, motor ordering           |
| `gps_params.yaml`       | M9N GPS config, compass, geofence          |
| `companion_params.yaml` | TELEM2 at 921600 baud for uXRCE-DDS        |
| `camera_params.yaml`    | Distance-based camera trigger every 5 m     |
| `tuning_params.yaml`    | PID gains (starting values)                |

!!! warning "Tuning Parameters"

    The values in `tuning_params.yaml` are **starting values only**. You must
    tune PID gains in flight using QGroundControl's PID tuning tools. Flying
    with un-tuned gains can cause oscillation or loss of control.
