# ADR-003: Rolling Shutter Camera (IMX477) over Global Shutter

## Status

Accepted

## Context

Photogrammetry requires high-resolution, geotagged images with good overlap.
Two camera options were evaluated for the Pi 5 CSI interface:

- **Pi Global Shutter Camera** — 1.6MP (1456×1088), global shutter, ~$50
- **Pi HQ Camera (IMX477)** — 12.3MP (4056×3040), rolling shutter, ~$50

Global shutter eliminates motion blur and rolling shutter distortion (jello effect),
which is important for fast-moving aerial photography. However, 1.6MP is extremely
low resolution for photogrammetry — it would produce very poor ground sample
distance (GSD) and detail.

## Decision

Use the **Raspberry Pi HQ Camera (IMX477)** with a **6mm CS-mount lens** despite
its rolling shutter.

## Consequences

**Positive:**

- **12.3MP** provides ~2cm/pixel GSD at 50-80m altitude — sufficient for
  site survey photogrammetry.
- **Interchangeable CS-mount lenses** — can swap to wider or narrower lens
  as needed.
- **Same price** as global shutter option (~$50 for camera, ~$20 for lens).
- **Well-supported** by libcamera on Pi 5.

**Negative:**

- **Rolling shutter distortion** — can cause jello effect at high speeds.
  Mitigated by flying survey missions at conservative speed (5 m/s cruise).
- **Motion blur** at very fast speeds — mitigated by short exposure times
  in good lighting conditions (outdoor survey).

**Neutral:**

- 12.3MP is more than enough for OpenDroneMap. Most survey drones use
  20MP cameras, but 12MP is the practical minimum.
- 6mm lens gives ~40mm equivalent FOV — good balance of coverage and detail.
