# Bennu Wiring Diagram

## Power Distribution

```
Battery (4S LiPo, XT60)
  │
  ├──► PM02 Power Module ──► Pixhawk 6C (POWER1 port)
  │         │
  │         └──► Voltage + Current sense to FC
  │
  ├──► ESC 4-in-1 (battery pads)
  │         │
  │         ├──► Motor 1 (Front Right)
  │         ├──► Motor 2 (Rear Left)
  │         ├──► Motor 3 (Front Left)
  │         └──► Motor 4 (Rear Right)
  │
  └──► BEC 5V 3A ──► Raspberry Pi 5 (GPIO 5V + GND pins 2,4,6)
```

## Signal Connections

```
Pixhawk 6C
  │
  ├── MAIN OUT 1-4 ──► ESC signal pads (DShot600)
  │
  ├── GPS1 (UART) ──► Holybro M9N GPS (JST-GH cable)
  │
  ├── TELEM1 ──► SiK Radio V3 (telemetry to ground station)
  │
  ├── TELEM2 ──► Raspberry Pi 5 UART
  │                TX (FC) ──► RX (Pi GPIO 15 / pin 10)
  │                RX (FC) ──► TX (Pi GPIO 14 / pin 8)
  │                GND ──► GND (Pi pin 6)
  │                (DO NOT connect 5V from TELEM2 — Pi powered by BEC)
  │
  ├── RC IN ──► ELRS 900MHz receiver (SBUS/CRSF)
  │
  └── I2C ──► (reserved for future sensors)

Raspberry Pi 5
  │
  ├── CSI connector ──► Pi HQ Camera (ribbon cable)
  │
  ├── GPIO 14/15 (UART) ──► Pixhawk TELEM2 (see above)
  │
  ├── USB-A ──► (optional: USB WiFi dongle for longer range)
  │
  └── microSD ──► 64GB card (image storage)
```

## Important Notes

1. **Cross-wire UART:** FC TX → Pi RX, FC RX → Pi TX
2. **Do NOT power Pi from TELEM2** — use dedicated BEC for clean 5V
3. **GPS mast height:** Mount GPS 10+ cm above electronics to reduce magnetic interference
4. **Motor direction:** Verify motor spin direction matches PX4 quad X layout before props on
5. **ESC signal ground:** Ensure ESC signal ground is common with FC ground
