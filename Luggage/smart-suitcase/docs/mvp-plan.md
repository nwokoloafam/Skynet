# Smart suitcase MVP — baseline plan

Version 2 · September 13, 2026

This is the current working plan, consolidated with the initial team draft and subsequent discussion. Numeric targets are preliminary engineering choices, not validated specifications. No motor, controller, or UWB purchase has been finalized for the loaded suitcase. The original Word draft is retained as a historical reference; this document takes precedence for current planning. See [hardware status](hardware-status.md), [draft review](draft-comparison.md), and [UWB shortlist](uwb-shortlist.md).

## 1. Objective and agreed constraints

Build a carry-on suitcase that follows a paired user and maintains proximity. The team has electrical and software engineering experience and prefers starting with UWB rather than cameras.

- Use existing **60 mm diameter wheels** (30 mm radius) for initial tests.
- Evaluate **four driven wheels controlled as left/right pairs**.
- Include manual joystick steering alongside autonomous following.
- Use **off-the-shelf electronics throughout the MVP**. Custom electronics are not a planned phase; reconsider only if testing establishes a specific limitation that available modules cannot reasonably address.
- Defer obstacle avoidance. Initially, a supervising user leads through flat indoor areas with generous clearance.
- Include reliable stopping, command timeouts, current limits, and fault handling from the first powered prototype.

**Mass assumption requiring confirmation:** calculations use 25 lb / 11.34 kg total loaded mass, including luggage, chassis, battery, and contents. If 25 lb means payload alone, recalculate using actual total mass.

## 2. Proposed operating envelope

| Item | Initial target |
|---|---|
| Environment | Flat indoor floors, wide turns, supervised operation |
| Test speed | Start at 0.3 m/s; qualify up to 0.8 m/s |
| Later speed investigation | 1.2 m/s, only after validation |
| Following distance | Initially about 1.2–1.5 m horizontally; define measurement reference points before testing |
| Target | One explicitly paired wearable tag |
| User stops | Decelerate and stop |
| Target too close | Stop; no automatic reverse initially |
| Tracking lost | Stop, indicate loss, verify reacquisition before resuming |
| Initial exclusions | Crowds, stairs, escalators, outdoor terrain, autonomous detours |

Following the user's current position can cut corners, even when the user walks around an obstacle. A later MVP phase follows a short history of the user's path to reduce this effect. That path is approximate and does not guarantee obstacle clearance.

## 3. UWB tracking approach

The robot needs **range and bearing**.

| Measurement | Principle | Result |
|---|---|---|
| Range | Timestamped two-way packet exchanges estimate time of flight | Distance to tag |
| Bearing | Suitable multi-antenna hardware measures arrival differences, commonly phase difference | Direction to tag within the calibrated field of view |
| Combined | Fuse range and bearing with motion estimates | Relative target position for following |

A single range measurement cannot determine steering direction. Several range-only radios on the suitcase could estimate position, but the short baseline makes angular estimates sensitive to range error. Prefer evaluating a supported range/PDoA reference design first.

### Proposed hardware arrangement

- User: battery-powered UWB tag, initially mounted outside clothing.
- Suitcase: reference hardware and firmware supporting two-way ranging and useful bearing measurement.
- Motion feedback: wheel encoders and an IMU.
- Manual controls: an off-the-shelf joystick/controller, initially separate from the tag.
- No installed building anchors required for this proposed relative range/bearing arrangement.

Qorvo's QM33120W is an example of a transceiver supporting two antenna ports, two-way ranging, and PDoA. This is a capability reference, not a selected component or complete ready-to-use tracking solution. Confirm development-kit availability, antenna configuration, firmware access, interoperability, and delivered measurements before purchasing.

The current first-bench recommendation is the complete Makerfabs MaUWB STM32 AoA Development Kit. Alternatives are the Makerfabs Gen2 anchor/tag and Qorvo QM33120WDK2. This is a recommendation, not an approved purchase. Gen1 and Gen2 Makerfabs parts are incompatible. The ordinary ESP32 DW3000 board from the draft does not establish bearing capability. See the shortlist for vendor links and previously observed prices.

### UWB feasibility tests

Measure range/bearing error, end-to-end latency, valid update rate, outliers, and dropouts across distance and angle. Test body orientations, back/side/pocket placement, intervening people, packed luggage, and motors running.

Validate front/back ambiguity, field of view, and elevation sensitivity. Slant range to a belt-mounted tag is not horizontal following distance. Resolve elevation or use an explicit height assumption and test its sensitivity. Do not assume one antenna baseline provides unambiguous 3D direction.

An AprilTag is a printed visual marker used by a calibrated camera to estimate pose. It is an alternative discussed earlier and is **not part of this UWB baseline**.

## 4. Mechanical and electrical architecture

| Subsystem | Baseline |
|---|---|
| Chassis | Rigid base, low battery placement, secure luggage attachment |
| Wheels | Four existing 60 mm wheels |
| Drive | Independent left/right commands; skid steering if all wheels have fixed orientation |
| Motors | Off-the-shelf geared motors with encoders; selection pending tests |
| Drivers | Off-the-shelf boards with current sensing/limiting and understood braking behavior |
| Controller | MCU development board for deterministic control, watchdogs, and faults |
| Additional compute | Optional single-board computer for development, estimation, and logging |
| Sensors | UWB reference hardware, encoders, IMU breakout |
| Power | Protected battery pack, fuse, main switch, DC/DC modules |
| Controls | Joystick, enable control, manual/follow selection, physical stop |
| Manual handling | Retain a practical way to roll/pull with power off |

Use the ordered small chassis for controls experiments before qualifying a drivetrain for 25 lb total mass. Do not assume its TT motors or frame support luggage loads. The draft reports an encoder wheel/LM393 ordered and Raspberry Pi/MCU hardware available; exact inventory needs confirmation.

Recommended development split: an available Pi for following, controls, and logging, with an MCU for deterministic feedback and stopping. UART is the initial interface candidate; define framing, sequence numbers, command age, heartbeat timeout, and fault reporting. Use Python for high-level work; choose timing-critical firmware or a purchased velocity controller after checking encoder capture and scheduling needs. No Jetson or custom PCB is required by this plan.

Evaluate the proposed L298N against motor current and voltage loss; a suitable MOSFET driver may be preferable. Fixed unpowered front wheels still scrub during turning and are not equivalent to casters. Size battery discharge capability separately from energy capacity, and test regulated logic power during starts, reversals, and loaded turns.

Two possible drive implementations:

1. Two motors, each mechanically driving both wheels on its side.
2. Four motors, each with its own driver and encoder loop; motors on a side receive the same nominal speed target.

Avoid assuming parallel-wired motors will have matched speed or current sharing.

Nominal differential commands are:

`v_left = v - yaw_rate × track_width / 2`

`v_right = v + yaw_rate × track_width / 2`

Convert linear wheel speed to angular speed using radius 0.03 m. Actual yaw behavior differs because skid steering involves lateral slip. Calibrate using measured motion.

**Turning scrub is an unresolved sizing issue.** Carpet, tire material, wheelbase, track width, and weight distribution can make turning much harder than straight rolling. Measure loaded turning current before finalizing motors. The 60 mm wheels also need separate floor-seam and threshold tests.

## 5. Preliminary force, torque, and speed calculations

### Assumptions

| Parameter | Value |
|---|---:|
| Total mass | 11.34 kg |
| Gravity | 9.81 m/s² |
| Wheel radius | 0.03 m |
| Acceleration | 0.5 m/s² |
| Illustrative rolling resistance, hard floor | 0.03 |
| Illustrative rolling resistance, carpet | 0.08 |
| Ramp case | 5 degrees |
| Load sharing | Equal across four driven wheels |

Straight-line force:

`F = m × a + Crr × m × g × cos(slope) + m × g × sin(slope)`

Wheel-output torque:

`torque_per_wheel = F × wheel_radius / 4`

| Condition | Total force | Torque per wheel | Combined torque per side |
|---|---:|---:|---:|
| Hard floor, constant speed | 3.34 N | 0.025 N·m | 0.050 N·m |
| Hard floor, accelerating | 9.01 N | 0.068 N·m | 0.135 N·m |
| Carpet, accelerating | 14.57 N | 0.109 N·m | 0.219 N·m |
| 5° ramp, hard floor, accelerating | 18.69 N | 0.140 N·m | 0.280 N·m |

These are approximate wheel-output requirements for straight travel. They exclude turning scrub, thresholds, drivetrain losses, and uneven loading. Replace assumed rolling resistance with measurements. For two motors, account for side-drive transmission losses. For motor-shaft torque, account for gear ratio and efficiency.

Provisional ranges to investigate—not validated requirements:

- Four motors: roughly 0.25–0.5 N·m continuous gearbox-output torque each.
- Two motors: roughly 0.5–1.0 N·m continuous output per side, plus transmission-loss allowance.

Loaded turning tests may require larger values. Verify available torque at operating speed, thermal limits, peak current, and gearbox ratings. Stall torque and no-load RPM alone are insufficient.

`wheel_RPM = 60 × ground_speed / (2 × pi × wheel_radius)`

| Ground speed | Wheel RPM |
|---|---:|
| 0.3 m/s | 95 |
| 0.8 m/s | 255 |
| 1.2 m/s | 382 |

For unchanged assumptions, straight-line forces and torques scale with total mass. Relative to the earlier 120 mm wheel calculation, 60 mm wheels halve geometric torque requirements and double RPM at the same ground speed; actual rolling resistance may change.

## 6. Software architecture and rates

```text
UWB → timestamped target measurements → estimator → following controller ┐
                                                                       ├→ mode arbitration
Joystick → manual velocity commands ───────────────────────────────────┘
        → speed/acceleration limits → left/right targets → motor loops

Encoder + IMU feedback → motion estimation and motor control
Fault handling overrides motion commands.
```

| Function | Proposed starting rate |
|---|---:|
| PWM | 20–25 kHz |
| Current control, if implemented | 10–20 kHz, coordinated with PWM/ADC |
| Wheel velocity loops | 500 Hz–1 kHz |
| IMU acquisition | 200–500 Hz |
| Estimator prediction / odometry | 100–200 Hz |
| Following controller | 50–100 Hz |
| Valid UWB range/bearing updates | Target 20–50 Hz; verify actual capability |
| Joystick commands | 50–100 Hz |

These are starting design targets, not requirements to replace adequate off-the-shelf controller internals. Loop sampling rate is not closed-loop bandwidth. Tune based on dynamics, encoder resolution, filtering, latency, and gearbox compliance. A faster estimator prediction rate does not create new sensor observations.

### Encoder speed estimation explained

At low speed, few encoder counts arrive in each 1 ms window. Example: 100 counts per wheel revolution at one revolution per second gives one count every 10 ms. Counting only in individual 1 ms windows produces mostly zeros with occasional spikes, despite steady movement.

Use time between encoder edges, a longer measurement window, or a suitable speed estimator. Account for the smoothing/latency tradeoff and explicitly detect stopping when edges cease. The control loop can still execute every 1 ms. Severity depends on effective counts per wheel revolution, including gearing and encoder decoding.

The draft links a 20 PPR DFRobot encoder. If mounted at wheel output, 60 mm wheels produce about 32 pulses/s at 0.3 m/s and 85 pulses/s at 0.8 m/s, or 31 ms and 12 ms between pulses. Verify the actual ordered sensor, counts, and direction sensing. Use it for bring-up, then decide whether higher-resolution quadrature feedback is needed. A 1 kHz loop does not create new encoder observations.

### Velocity and current loops explained

- Outer velocity loop: compares requested and measured speed, then requests motor current/torque.
- Inner current loop: compares requested and measured current, then adjusts motor voltage through PWM.

Current approximately determines motor torque. These loops can reside inside a purchased controller. Prefer an off-the-shelf controller providing encoder-based speed control and current limiting; confirm whether it also implements a true current loop. Current limiting alone is not the same as current regulation.

The MCU/controller must independently handle stale commands and stop inputs. Do not make a Linux process the sole stopping mechanism.

## 7. Modes and following behavior

| State | Behavior |
|---|---|
| Idle | Stationary, awaiting selection |
| Manual | Joystick controls forward speed and yaw rate; hold-to-drive |
| Acquire | Verify paired target and stable measurements |
| Follow | Maintain gap and track direction or recent path |
| Paused | Stationary until deliberate resume |
| Target lost | Stop and indicate loss; verify reacquisition |
| Fault | Stop; reset according to the fault |

Use explicit arbitration between manual and follow modes. Initially require deliberate resume after target loss; revisit automatic resume only after defining and validating its conditions.

Initial following logic:

- Estimate target position and relative velocity with timestamped measurements.
- Reject implausible jumps and maintain confidence/measurement age.
- Use a deadband around the desired gap.
- Limit acceleration and yaw rate.
- Slow for large bearing errors or degraded confidence.
- Stop when too close; do not reverse automatically.
- Stop on stale or unreliable tracking.

Next, store a short user-path history in local odometry coordinates and follow it. IMU yaw helps with skid-steer odometry, but does not eliminate drift. Discard stale or implausible path estimates.

## 8. Implementation phases

Planning estimates assume two engineers and exclude major procurement delays. Begin with hardware inventory and interface definitions. Phases 0 and 1 can proceed in parallel. Small-chassis results prove control behavior only; full-load capability is qualified separately.

| Phase | Work | Exit criterion |
|---|---|---|
| 0 — UWB feasibility, 1–2 weeks | Reference radios, tag, mounts, calibration, logger | Quantified errors, latency, valid update rate, ambiguity, and dropouts over a defined envelope |
| 1 — Manual chassis and speed control, ~2 weeks | Ordered chassis, 60 mm wheels, encoders, battery, joystick, watchdogs, speed loops, IMU logging | Manual and regulated-speed driving at prototype mass; current, braking, turning, and brownouts measured |
| 2 — Basic following, 1–2 weeks | Target estimator, gap/bearing control, confidence handling | Smooth straight following and gentle turns; reliable stop on tracking loss |
| 3 — Path following, ~2 weeks | Local odometry, recent path history, path controller | Reduced corner cutting on a measured course |
| 4 — Loaded drivetrain and suitcase integration, 2–3 weeks plus hardware lead time | Select/qualify drivetrain for target total mass; packaging, antenna clearance, battery access, manual handling | Measured driving, turning, braking, and thermal performance at target mass across loads and tag placements |
| 5 — Supervised testing, duration based on results | Longer sessions and structured fault tests | Written acceptance criteria met with recorded evidence |

**Custom electronics are excluded from this roadmap.** Reconsider only when measured evidence identifies a concrete limitation in available modules.

## 9. Validation, logging, and stopping

Log raw UWB measurements/quality, timestamps, estimated target position, wheel commands and feedback, IMU measurements, current, voltage, and stop reasons.

Test sudden stops/turns, occlusion, radio disconnection, controller/process failures, stale commands, joystick release, mode changes, low battery, wheel jams, carpet turns, uneven packing, and target reacquisition.

Proposed early tracking target: steady straight-line gap error within approximately ±0.3 m. Establish final acceptance thresholds after phase 0 and chassis measurements.

Stopping-distance approximation:

`d_stop = speed × total_latency + speed² / (2 × braking_deceleration)`

At 0.8 m/s, 150 ms total latency, and 1 m/s² deceleration:

`d_stop ≈ 0.12 + 0.32 = 0.44 m`

This is illustrative, before margin. Include sensing age, filtering, decision time, communication, and actuator response in latency. Measure actual stopping distance with intended load and surfaces. Distinguish braking from coasting; verify driver and battery behavior during braking. Define what the physical stop does and test it.

## 10. Optional extensions

| Extension | Purpose |
|---|---|
| Forward ToF/depth sensing | Stop for detected obstacles |
| Downward sensing | Detect some drop-offs; validate separately |
| LiDAR/depth and local planner | Navigate around obstacles |
| Additional UWB coverage | Improve tracking across orientations and turns |
| Integrated wearable controls/haptics | Steering, pause, and loss feedback |

Optional forward ToF stopping may be added during early following tests, with an MCU-level stop override. It must be tested for coverage and missed detections; it is not a guarantee against collision. Defer autonomous detours until following is repeatable. Obstacle avoidance is not a prerequisite for full-load qualification or suitcase integration.

## 11. Open decisions for comparison with team ideas

| Decision | Current baseline / missing information |
|---|---|
| Mass | 25 lb total assumed; confirm payload versus total |
| Drive topology | Four wheels; two mechanically coupled motors versus four motors unresolved |
| Geometry | Wheelbase, track width, ground clearance, and center of mass needed |
| Existing hardware | Chassis and encoder reported ordered; verify delivered motor specs, actual encoder, driver, and battery; see hardware-status.md |
| UWB platform | Makerfabs STM32 AoA kit recommended; purchase and selection unconfirmed |
| Wearable location | External mounting initially; test acceptable placements |
| Compute | Pi plus MCU recommended for development; exact available boards and firmware language pending |
| Runtime | Required operating duration not specified |
| Manual controls | Off-the-shelf joystick/controller to select |
| Acceptance | Final error, stop-distance, and dropout criteria to establish |

For each new idea, compare its benefit, changes to the baseline, hardware/software effort, critical assumptions, and a small experiment that would validate it.

## References

Sources consulted during the planning discussion; design targets and calculations above are our preliminary engineering estimates.

- [Qorvo QM33120W capabilities](https://www.qorvo.com/products/p/QM33120W)
- [AprilTag implementation and pose estimation](https://github.com/AprilRobotics/apriltag)
- [ODrive cascaded controller documentation](https://docs.odriverobotics.com/v/latest/manual/control.html)
- [CMU experimental comparison of skid steering](https://www.ri.cmu.edu/pub_files/pub1/shamah_benjamin_1999_1/shamah_benjamin_1999_1.pdf)
