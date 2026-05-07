# Obstacle Avoidance

## Why Bennu Does Not Include Obstacle Avoidance

Bennu is a survey drone that flies pre-planned grid missions at **50--80m altitude**. At survey altitude, there are no obstacles to avoid — the drone is well above trees, buildings, and towers. This matches how the entire commercial survey drone industry operates.

## Safety Without Obstacle Sensors

Bennu relies on **flight planning discipline and PX4 failsafes** instead of obstacle sensors:

| Safety Feature | Mechanism |
|---|---|
| Fly above obstacles | Survey altitude (50--80m) clears all ground obstacles |
| Geofence | PX4 enforces max distance (200m) and max altitude (120m) from home |
| RTL on RC loss | Automatic return-to-launch if RC signal is lost |
| RTL on data link loss | Automatic return-to-launch if telemetry link drops |
| Battery RTL | Returns at 25% battery, lands at 10% emergency |
| RTL altitude | Returns at 30m — set above known obstacles near launch point |
| Pre-flight site survey | Pilot identifies power lines, towers, and tall trees before flight |

!!! warning "Power Lines"
    Power lines are the #1 cause of survey drone crashes. No consumer obstacle avoidance sensor can reliably detect thin wires. The only mitigation is pre-flight planning — identify and mark all power lines in the survey area.

## When Obstacle Avoidance Would Be Needed

| Mission Type | Altitude | Obstacle Risk | Avoidance Needed? |
|---|---|---|---|
| Photogrammetry survey | 50--80m | None | No |
| Infrastructure inspection | 5--20m | High | Yes |
| Indoor/confined mapping | 1--5m | Very high | Yes |
| Urban mapping between buildings | 20--40m | Medium | Maybe |

## Future: Adding Obstacle Avoidance

If Bennu is extended for low-altitude inspection work (Config B: RGB + thermal), obstacle avoidance sensors can be added. PX4 supports obstacle avoidance via the `px4_avoidance` ROS2 package, which requires a depth sensor connected to the companion computer.

| Sensor | Range | Weight | Price | Notes |
|---|---|---|---|---|
| Luxonis OAK-D Lite | 0.3--15m | 61g | ~$150 | Best value — stereo depth + onboard AI |
| Intel RealSense D435i | 0.3--10m | 72g | ~$300 | Proven, well-supported |
| Benewake TF02-Pro | 0.1--40m | 12g | ~$60 | Single-point LiDAR (altitude hold only) |

Adding a depth camera costs ~60g of weight (~2 min flight time) and requires the ROS2 companion computer (Pi 4) to run the avoidance planner. This is a future upgrade, not part of the initial build.
