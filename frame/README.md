# Bennu Drone Frame — 7" Quadcopter

## Base Frame

**TBS Source One V5 7" Deadcat** — open-source carbon fiber frame.

- **Source files:** https://github.com/tbs-trappy/source_one (DXF, STL)
- **Buy pre-cut:** available from GetFPV, Pyrodrone, TBS store (~$35-45)
- **Prop size:** 7 inch (HQProp 7x3.5x3)
- **Motor-to-motor diagonal:** ~320mm
- **Frame weight:** ~144g
- **Stack mount:** 30.5x30.5mm (fits Pixhawk 6C and Tekko32 ESC)
- **Layout:** Deadcat (props out of camera view)

## Custom Adapter Parts (3D-printed)

The Source One V5 provides the structural frame. These custom parts adapt it for the Bennu photogrammetry payload:

| Part | Est. Print Time | Notes |
|------|----------------|-------|
| Pi 4 top plate adapter | ~1.5h | Mounts Pi 4 (85x56mm) above FC stack |
| Camera mount | ~1h | Bottom-mount, 15° forward tilt for IMX477 |
| GPS mast base | ~30min | Clips onto rear standoffs, holds 12mm CF tube |
| Canopy | ~2h | Protects Pi 4 + wiring from wind/debris |

## Print Settings

- **Material:** CF-PETG (e.g., Polymaker PolyLite CF-PETG)
- **Nozzle:** 0.4mm hardened steel (CF wears brass nozzles)
- **Layer height:** 0.2mm
- **Perimeters:** 3-4
- **Infill:** 30-40% gyroid
- **Bed temp:** 80°C
- **Nozzle temp:** 240-250°C

## CAD Files

- `step/` — Editable STEP files for custom adapters (FreeCAD or Fusion 360)
- `stl/` — Print-ready STL files for custom adapters
