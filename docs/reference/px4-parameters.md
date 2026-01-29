# PX4 Parameters

Bennu's PX4 parameters are organized into 6 YAML files, applied in order via `upload_params.sh`. Source files are in `firmware/px4/params/`.

=== "Base"

    Core airframe, EKF2, failsafe, and battery parameters.

    | Parameter | Value | Description |
    |---|---|---|
    | `SYS_AUTOSTART` | `4001` | Generic Quadcopter X airframe |
    | `EKF2_AID_MASK` | `1` | GPS only |
    | `EKF2_HGT_REF` | `1` | GPS height reference |
    | `EKF2_GPS_V_NOISE` | `0.5` | GPS velocity noise |
    | `EKF2_GPS_P_NOISE` | `0.5` | GPS position noise |
    | `EKF2_BARO_NOISE` | `3.5` | Barometer noise |
    | `COM_DL_LOSS_T` | `10` | Data link loss timeout (seconds) |
    | `NAV_DLL_ACT` | `0` | Data link loss action: return to launch |
    | `NAV_RCL_ACT` | `2` | RC loss action: return to launch |
    | `COM_RCL_EXCEPT` | `0` | No RC loss exceptions |
    | `RTL_RETURN_ALT` | `30` | RTL altitude (meters) |
    | `RTL_DESCEND_ALT` | `10` | RTL descend altitude (meters) |
    | `RTL_LAND_DELAY` | `5` | Delay before landing at RTL (seconds) |
    | `BAT_LOW_THR` | `0.25` | Low battery warning at 25% |
    | `BAT_CRIT_THR` | `0.15` | Critical battery at 15% |
    | `BAT_EMERGEN_THR` | `0.10` | Emergency battery at 10% |
    | `COM_LOW_BAT_ACT` | `2` | Low battery action: return to launch |
    | `COM_ARM_WO_GPS` | `0` | Require GPS to arm |
    | `COM_ARM_EKF_POS` | `0.5` | EKF position error threshold for arming |

=== "Motor"

    Motor, ESC, and DShot configuration.

    | Parameter | Value | Description |
    |---|---|---|
    | `DSHOT_CONFIG` | `600` | DShot600 protocol |
    | `MOT_ORDERING` | `0` | PX4 default motor ordering |
    | `THR_MDL_FAC` | `0.3` | Thrust model factor (tune after first flights) |
    | `PWM_MAIN_MIN` | `1000` | PWM minimum (fallback if not using DShot) |
    | `PWM_MAIN_MAX` | `2000` | PWM maximum (fallback if not using DShot) |

    **Motor ordering (PX4 Quad X):**

    | Position | Motor | Direction |
    |---|---|---|
    | Front Right | Motor 1 | CCW |
    | Rear Left | Motor 2 | CCW |
    | Front Left | Motor 3 | CW |
    | Rear Right | Motor 4 | CW |

=== "GPS"

    GPS module and geofence configuration.

    | Parameter | Value | Description |
    |---|---|---|
    | `GPS_1_CONFIG` | `201` | GPS on UART port (GPS1) |
    | `GPS_1_PROTOCOL` | `1` | u-blox protocol |
    | `GPS_1_GNSS` | `7` | GPS + GLONASS + Galileo |
    | `CAL_MAG0_EN` | `1` | Enable internal compass |
    | `CAL_MAG1_EN` | `1` | Enable external compass (GPS module) |
    | `CAL_MAG_PRIME` | `1` | Use external compass as primary |
    | `EKF2_MAG_TYPE` | `1` | Automatic magnetometer selection |
    | `GF_ACTION` | `1` | Geofence action: warning |
    | `GF_MAX_HOR_DIST` | `500` | Max horizontal distance (meters) |
    | `GF_MAX_VER_DIST` | `120` | Max vertical distance (meters) |

=== "Companion"

    Companion computer (Pi 5) connection via TELEM2.

    | Parameter | Value | Description |
    |---|---|---|
    | `MAV_1_CONFIG` | `102` | TELEM2 port |
    | `SER_TEL2_BAUD` | `921600` | 921600 baud for uXRCE-DDS |
    | `MAV_1_MODE` | `2` | Onboard mode |
    | `UXRCE_DDS_CFG` | `102` | Enable uXRCE-DDS on TELEM2 |
    | `UXRCE_DDS_AG_IP` | `0` | Not used for serial |

=== "Camera"

    Camera trigger configuration for distance-based capture.

    | Parameter | Value | Description |
    |---|---|---|
    | `TRIG_INTERFACE` | `3` | MAVLink trigger (sends to companion) |
    | `TRIG_MODE` | `4` | Distance-based trigger |
    | `TRIG_DIST` | `5.0` | Trigger every 5 meters (adjust per mission) |
    | `TRIG_ACT_TIME` | `0.5` | Trigger activation time (seconds) |
    | `TRIG_MIN_INTERVA` | `1.0` | Minimum interval between triggers (seconds) |
    | `CAM_CAP_FBACK` | `1` | Enable capture feedback |

=== "Tuning"

    PID gains, attitude, position, and speed limits.

    !!! warning "Starting Values"
        These are starting values --- tune via autotune (`MC_AT_START=1`) or manual tuning after maiden flight.

    **Rate controller (inner loop):**

    | Parameter | Value | Description |
    |---|---|---|
    | `MC_ROLLRATE_P` | `0.15` | Roll rate P gain |
    | `MC_ROLLRATE_I` | `0.2` | Roll rate I gain |
    | `MC_ROLLRATE_D` | `0.003` | Roll rate D gain |
    | `MC_PITCHRATE_P` | `0.15` | Pitch rate P gain |
    | `MC_PITCHRATE_I` | `0.2` | Pitch rate I gain |
    | `MC_PITCHRATE_D` | `0.003` | Pitch rate D gain |
    | `MC_YAWRATE_P` | `0.2` | Yaw rate P gain |
    | `MC_YAWRATE_I` | `0.1` | Yaw rate I gain |
    | `MC_YAWRATE_D` | `0.0` | Yaw rate D gain |

    **Attitude controller (outer loop):**

    | Parameter | Value | Description |
    |---|---|---|
    | `MC_ROLL_P` | `6.5` | Roll attitude P gain |
    | `MC_PITCH_P` | `6.5` | Pitch attitude P gain |
    | `MC_YAW_P` | `2.8` | Yaw attitude P gain |

    **Position controller:**

    | Parameter | Value | Description |
    |---|---|---|
    | `MPC_XY_P` | `0.95` | Horizontal position P gain |
    | `MPC_Z_P` | `1.0` | Vertical position P gain |
    | `MPC_XY_VEL_P_ACC` | `1.8` | Horizontal velocity P gain |
    | `MPC_Z_VEL_P_ACC` | `4.0` | Vertical velocity P gain |

    **Speed limits (conservative for survey):**

    | Parameter | Value | Description |
    |---|---|---|
    | `MPC_XY_CRUISE` | `5.0` | Cruise speed (m/s) |
    | `MPC_XY_VEL_MAX` | `8.0` | Max horizontal speed (m/s) |
    | `MPC_Z_VEL_MAX_UP` | `3.0` | Max ascent speed (m/s) |
    | `MPC_Z_VEL_MAX_DN` | `1.5` | Max descent speed (m/s) |
    | `MPC_TILTMAX_AIR` | `35` | Max tilt angle (degrees) |
    | `MC_AT_START` | `0` | Set to 1 to start autotune in flight |
