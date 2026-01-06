# Build Guide — Step 1: Frame Assembly

## Prerequisites

- All frame parts 3D printed (see frame/README.md)
- Carbon fiber tubes cut to length
- M3 heat-set inserts installed in printed parts
- Tools: hex drivers, soldering iron (for heat-set inserts), CA glue

## Assembly Order

### 1. Install Heat-Set Inserts

Install M3 heat-set inserts into all screw holes on the bottom plate, top plate,
and arm clamps. Use a soldering iron at 220°C, press straight in.

### 2. Assemble Arms

1. Slide CF tube arms through the bottom plate channels
2. Attach arm clamps on both sides of each arm
3. Tighten M3 screws — snug, not overtight (CF cracks)
4. Attach motor mounts to the ends of each arm

### 3. Mount ESC

1. Place 4-in-1 ESC on bottom plate
2. Secure with M3 screws or double-sided tape
3. Route motor wires through arm channels

### 4. Mount Flight Controller

1. Attach vibration dampening balls to M2.5 standoffs
2. Secure FC mount standoffs to top plate
3. Place Pixhawk 6C on standoffs, secure with rubber grommets
4. Arrow on FC pointing forward

### 5. GPS Mast

1. Insert 12mm CF tube into GPS mast base
2. Secure with set screw or CA glue
3. Mount M9N GPS module on top with double-sided tape
4. Route GPS cable down the mast, secure with zip ties

### 6. Camera Mount

1. Attach camera mount bracket to bottom plate (15° forward tilt)
2. Pi HQ Camera module mounts with M2 screws
3. Route CSI ribbon cable up through the frame to Pi location

### 7. Stack Top Plate

1. Place top plate over standoffs
2. Secure with M3 screws
3. Pi 5 mounts on top plate with M2.5 standoffs

### 8. Landing Gear

1. Clip landing legs onto bottom plate corners
2. Verify clearance for camera underneath

## Weight Target

| Component | Weight |
|-----------|--------|
| Frame (printed + CF) | ~180g |
| Motors (×4) | ~120g |
| ESC 4-in-1 | ~30g |
| Pixhawk 6C | ~40g |
| GPS M9N | ~25g |
| Pi 5 + camera | ~100g |
| Battery 4S 2200mAh | ~220g |
| Wiring, props, misc | ~80g |
| **Total AUW** | **~795g** |

Target AUW under 900g for good flight efficiency on 7" props.
