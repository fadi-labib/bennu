# Vibration Damping

Camera vibration isolation for sharp aerial images on the Bennu drone.

## Why It Matters

The Raspberry Pi HQ Camera uses a **rolling shutter** (IMX477). Rolling shutter sensors are sensitive to vibration — high-frequency vibrations cause:

- Jello effect (wobbly distortion in video/images)
- Motion blur from micro-movements during exposure
- Reduced Laplacian variance (detected as "blur" by quality scoring)

## Damping Strategy

### Camera Mount

The camera mount uses **TPU (flexible filament) vibration isolators** between the rigid CF-PETG frame and the camera plate:

```
Frame (CF-PETG, rigid)
  │
  ├── TPU damper pads (4x, Shore 95A)
  │
  └── Camera plate (CF-PETG)
        └── HQ Camera + 6mm lens
```

### Design Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Damper material | TPU Shore 95A | Soft enough to isolate, firm enough to not oscillate |
| Damper count | 4 | One per corner of camera plate |
| Damper height | 6mm | Provides ~2mm compression under load |
| Camera mass | ~45g | HQ Camera + 6mm CS-mount lens |
| First resonance | ~25 Hz (estimated) | Below typical prop frequencies (~80-150 Hz) |

### Motor Balancing

Propeller and motor imbalance is the primary vibration source. Before flight:

1. **Balance propellers** using a magnetic balancer
2. **Check motor screws** — loose screws amplify vibration
3. **Verify prop adapters** — collets must be tight

### PX4 Vibration Monitoring

PX4 reports vibration levels via the `estimator_status` topic:

- **Good:** < 15 m/s² peak
- **Marginal:** 15–30 m/s² — damping may need improvement
- **Bad:** > 30 m/s² — flight controller may reject GPS fusion

Check in QGroundControl: *Analyze → Vibration*

## Testing

After assembly, verify vibration isolation:

1. Power on, arm (props removed), throttle to 50%
2. Check PX4 vibration in QGC
3. Take a test image — check Laplacian variance > 100 (sharp)
4. If blurry: increase TPU damper thickness or switch to softer Shore rating
