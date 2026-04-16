# Frame Specifications

The Bennu frame uses a TBS Source One V5 7" Deadcat as the base, with custom 3D-printed adapter parts for the companion computer, camera, and GPS mast.

## Base Frame: TBS Source One V5 7" DC

| Spec | Value |
|---|---|
| Type | 7" Deadcat (props out of camera view) |
| Diagonal (M2M) | ~320mm |
| Weight | ~144g |
| Arm thickness | 6mm |
| Top plate | 2mm carbon fiber |
| Bottom plate | 2.5mm carbon fiber |
| FC/ESC stack mount | 30.5x30.5mm and 20x20mm |
| Open-source files | [GitHub](https://github.com/tbs-trappy/source_one) (DXF, STL) |

!!! tip "Why Deadcat?"
    The deadcat layout angles the front arms backward so propellers do not appear in downward-facing camera images. This is essential for photogrammetry — props in frame create artifacts in orthomosaics.

## Custom 3D-Printed Adapters

These parts are printed in CF-PETG and mount onto the Source One V5 frame.

| Part | Est. Print Time | Notes |
|---|---|---|
| Pi 4 top plate adapter | ~1.5h | Mounts Pi 4 (85x56mm) above the FC stack on M2.5 standoffs |
| Camera mount | ~1h | Bottom-mount for IMX477, 15° forward tilt |
| GPS mast base | ~30min | Clips onto rear standoffs, holds 12mm CF tube vertical |
| Canopy | ~2h | Protects Pi 4 + wiring from wind/debris |

## Print Settings

| Setting | Value |
|---|---|
| Layer height | 0.2mm |
| Perimeters | 3--4 |
| Infill | 30--40% gyroid |
| Nozzle temp | 240--250°C |
| Bed temp | 80--85°C |
| Material | CF-PETG |

!!! tip "Nozzle"
    Use a 0.4mm hardened steel nozzle. Carbon fiber filament wears out brass nozzles quickly.

## Non-Printed Components

| Part | Qty | Notes |
|---|---|---|
| CF tube 12mm OD x 150mm | 1 | GPS mast |
| M3x8 button head screws | 8 | Adapter mounting |
| M3 heat-set inserts | 8 | Press into printed adapters |
| M2.5x6 screws | 4 | Pi 4 mounting |
| M2.5 standoffs 10mm | 4 | FC vibration mount (included with Pixhawk 6C) |
| Vibration dampening balls | 4 | FC soft mount |

## Target Weight

| | Weight |
|---|---|
| Source One V5 7" DC frame | ~144g |
| 3D-printed adapters (all) | ~30g |
| **Total frame weight** | **~174g** |
| Target AUW (with 2200mAh) | <750g |
| Target AUW (with 3000mAh) | <830g |
