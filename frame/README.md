# Bennu Drone Frame — 7" Quadcopter

## Specifications

- **Prop size:** 7 inch (HQProp 7x3.5x3)
- **Motor-to-motor diagonal:** ~300mm
- **Material:** CF-PETG (carbon fiber reinforced PETG)
- **Arms:** 10mm OD carbon fiber tubes (NOT 3D printed)
- **Fits print bed:** 235×235mm (AnkerMake M5C)

## Design Approach

The frame is a hybrid design:
- **3D-printed body** (center plates, motor mounts, canopy, camera mount, GPS mast base)
- **Carbon fiber tube arms** (10mm OD, ~5mm wall) for strength and vibration damping

## Parts List (printed)

| Part | Qty | Est. Print Time | Notes |
|------|-----|----------------|-------|
| Bottom plate | 1 | ~3h | Battery mount, ESC mount |
| Top plate | 1 | ~2h | Pi 5 mount (M2.5 holes), FC mount |
| Motor mount | 4 | ~30min each | Press-fit onto CF tubes |
| Arm clamp | 4 | ~20min each | Secures CF tubes to body |
| GPS mast base | 1 | ~30min | Holds 12mm CF tube vertical |
| Camera mount | 1 | ~1h | Bottom-mount, 15° forward tilt |
| Canopy | 1 | ~2h | Protects FC + Pi + wiring |
| Landing legs | 4 | ~20min each | Simple clip-on legs |

## Non-printed Parts

| Part | Qty | Notes |
|------|-----|-------|
| CF tube 10mm OD × 200mm | 4 | Drone arms |
| CF tube 12mm OD × 150mm | 1 | GPS mast |
| M3×8 button head screws | 20 | Frame assembly |
| M3 press-fit inserts | 20 | Heat-set into prints |
| M2.5×6 screws | 4 | Pi 5 mounting |
| M2.5 standoffs 10mm | 4 | FC vibration mount |
| Vibration dampening balls | 4 | FC soft mount |

## Print Settings

- **Material:** CF-PETG (e.g., Polymaker PolyLite CF-PETG)
- **Nozzle:** 0.4mm hardened steel (CF wears brass nozzles)
- **Layer height:** 0.2mm
- **Perimeters:** 3-4
- **Infill:** 30-40% gyroid
- **Bed temp:** 80°C
- **Nozzle temp:** 240-250°C

## CAD Files

- `step/` — Editable STEP files (open in FreeCAD or Fusion 360)
- `stl/` — Print-ready STL files
