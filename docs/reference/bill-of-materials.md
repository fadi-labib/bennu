# Bill of Materials

Complete parts list for the Bennu 7" photogrammetry quadcopter.

!!! info "Pricing"
    Prices estimated as of 2026. Total: **~$550--750** excluding RC transmitter and 3D printer.

## Frame (~$50--70)

| Component | Part | Price | Notes |
|---|---|---|---|
| Base frame | TBS Source One V5 7" Deadcat | $35--45 | Open-source carbon fiber frame, 30.5mm stack, deadcat = no props in camera view |
| GPS mast base | 3D printed (CF-PETG) | ~$2 filament | Clips onto rear standoffs, holds 12mm CF tube |
| Pi 4 top plate adapter | 3D printed (CF-PETG) | ~$2 filament | Mounts Pi 4 above FC stack on standoffs |
| Camera mount | 3D printed (CF-PETG) | ~$2 filament | Bottom-mount, 15° forward tilt for IMX477 |
| Canopy | 3D printed (CF-PETG) | ~$3 filament | Protects Pi 4 and wiring |
| CF tube 12mm OD x 150mm | GPS mast | $5 | Vertical mast for GPS antenna |
| M3 hardware + heat-set inserts | Assorted | $10 | Frame assembly |

## Flight Controller & Core Electronics (~$350--400)

| Component | Part | Price | Notes |
|---|---|---|---|
| Flight Controller | Holybro Pixhawk 6C | $110--150 | STM32H743, dual IMU, PX4 reference board, TELEM2 for companion |
| ESC | Holybro Tekko32 F4 4-in-1 50A | $60--80 | BLHeli_32, DShot600 |
| Motors | T-Motor Velox V2207.5 1950KV x4 | $50--60 | Efficient at 7", well-proven |
| Props | HQProp 7x3.5x3 tri-blade x4+ spares | $15 | Good thrust/efficiency at survey speed |
| GPS | Holybro M9N (u-blox M9N) | $40--50 | PX4-native, built-in compass |
| RC Receiver | TBS Crossfire Nano or ELRS 900MHz | $25--40 | Long range >10km |
| Battery | 4S 2200--3000mAh LiPo x2 | $50--70 | ~15--20 min flight per battery |
| Power Module | Holybro PM02 | included | Current/voltage sensing |
| Telemetry | Holybro SiK Radio V3 (433/915MHz) | $40--50 | MAVLink to QGC |

## Camera System (~$70)

| Component | Part | Price | Notes |
|---|---|---|---|
| Camera | Raspberry Pi HQ Camera (IMX477) | $50 | 12.3MP, CS-mount, ~35g |
| Lens | 6mm CS-mount | $20 | ~2cm/pixel GSD at 50--80m |

## Companion Computer (~$75)

| Component | Part | Price | Notes |
|---|---|---|---|
| Computer | Raspberry Pi 4 (4GB) | $55 | ROS2, uXRCE-DDS, libcamera |
| Storage | 64GB+ microSD | $10--15 | Image storage during flight |
| Power | BEC 5V 3A | $5--10 | Dedicated BEC from battery voltage |

## Weight Budget

| Component | Weight |
|---|---|
| Source One V5 7" DC frame | ~144g |
| 4x T-Motor V2207.5 | ~120g |
| Tekko32 4-in-1 ESC | ~12g |
| Pixhawk 6C + PM02 | ~55g |
| M9N GPS + mast | ~30g |
| RC receiver + SiK radio | ~20g |
| Raspberry Pi 4 + SD card | ~46g |
| IMX477 + lens | ~40g |
| BEC + wiring + connectors | ~35g |
| 3D printed adapters | ~30g |
| **Dry weight** | **~530g** |
| 4S 2200mAh battery | ~200g |
| **AUW (2200mAh)** | **~730g** |
| 4S 3000mAh battery | ~280g |
| **AUW (3000mAh)** | **~810g** |
