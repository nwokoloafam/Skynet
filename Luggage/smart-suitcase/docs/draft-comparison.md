# Initial team draft compared with the baseline

Recorded September 13, 2026. This review explains the corrections and recommendations incorporated into version 2 of the [working plan](mvp-plan.md). Hardware selections remain pending; inclusion is not a claim of purchase or validation. The original draft is preserved unchanged in [reference/initial-team-draft.docx](reference/initial-team-draft.docx).

## Agreements and useful additions

- Small RC chassis for initial development, with separate qualification at 25 lb total loaded mass.
- Pi for behavior/logging and MCU for motor feedback, command timeouts, and stopping.
- UART is a reasonable initial interface; include framing, sequence numbers, and stale-command handling.
- Optional MCU-level ToF obstacle stopping can precede full avoidance.
- Test brownouts during starts, reversals, and loaded turns.
- Current agreed constraint: off-the-shelf electronics only unless a measured limitation proves custom hardware necessary.

## Proposed changes

- Move UWB range and bearing feasibility to the beginning, in parallel with chassis work.
- Install encoders during drive bring-up; qualify their resolution before relying on low-speed control.
- Log IMU yaw during drivetrain testing; UWB target measurements do not replace measuring chassis rotation.
- Remove obstacle avoidance as a prerequisite for loaded suitcase integration.
- Use Python for high-level logic and tools; benchmark timing-critical firmware or use an off-the-shelf velocity controller.
- Fixed unpowered front wheels still scrub during turns; they are not equivalent to swivel casters.

## Calculation corrections

- Force at the contact patch is torque divided by wheel radius. Larger wheels give less force at fixed torque.
- Per-wheel torque is total required wheel torque divided by number of driven wheels, assuming equal sharing; do not divide torque by radius to distribute it.
- Apply gear ratio and efficiency only when converting motor-shaft torque to output torque. Do not multiply a gearbox-output rating by gear ratio again.
- Stall torque is not continuous available torque at operating speed.
- The draft's 0.8 kgf·cm corresponds to approximately 0.078 N·m. If this is gearbox-output stall torque, it is close to the baseline's 0.068 N·m per-wheel accelerating hard-floor requirement, leaving insufficient justification for loaded use at speed or while turning.
- The draft's 0.686 gf·cm figure needs verification against the original specification.
- Determine whether traction, torque, driver current, or turning scrub limits performance by measurement.
- One motor does not inherently save power; required mechanical work and system efficiency govern consumption.

## Encoder implications

The linked [DFRobot kit](https://www.dfrobot.com/product-98.html) specifies 20 pulses per revolution. Assuming wheel-output measurement with 60 mm wheels, 0.3 m/s produces approximately 32 pulses/s (31 ms between pulses), while 0.8 m/s produces approximately 85 pulses/s (12 ms between pulses). A 1 kHz control loop therefore executes many times between new observations. Use edge timing or appropriate estimation and quantify latency. Verify actual ordered hardware and whether it senses direction independently; consider higher-resolution quadrature encoders for the loaded platform.

## Driver and battery notes

The [L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf) shows substantial bridge voltage drop, relevant to low-voltage motors. Evaluate a suitable MOSFET driver before final selection.

Battery energy is measured in Wh, not W: 7.4 V nominal at 2–3 Ah is 14.8–22.2 Wh. Capacity and discharge capability are separate requirements. The aviation threshold discussed is 100 Wh, with additional conditions for smart baggage and removable batteries; consult [FAA battery guidance](https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries) and [smart-baggage guidance](https://www.faa.gov/hazmat/packsafe/baggage-with-lithium-batteries) before travel-oriented design decisions.

## Proposed combined sequence

1. Inventory hardware, verify specifications, and define Pi/MCU interface.
2. In parallel: UWB range/bearing bench tests and manual chassis/encoder/battery/watchdog bring-up.
3. Closed-loop speed control and current, braking, turning, and brownout tests.
4. Basic following and target-loss handling; optional ToF stopping.
5. IMU/odometry integration and recent-path following.
6. Drivetrain qualification at total target mass and suitcase integration.
7. Optional obstacle avoidance.
