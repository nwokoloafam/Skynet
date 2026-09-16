# Hardware status and next actions

Updated September 13, 2026. Status reflects the conversation and original draft, not a physical inventory check.

| Item | Known status | Next action |
|---|---|---|
| Wheels | User reports 60 mm wheels available for testing | Measure actual diameter and attachment |
| Small 4WD chassis | Marked ordered in team draft | Confirm delivered kit, wheelbase, track width, weight, and motor part numbers |
| Encoder wheel and LM393 | Marked ordered; draft links a 20 PPR DFRobot kit | Confirm actual sensor, mounting, counts per wheel revolution, and direction capability |
| Motors | Draft mentions TT, 1:48, 0.8 kgf·cm stall at 6 V; exact specifications unverified | Obtain output torque-speed/current ratings; do not assume loaded suitability |
| Pi and MCU boards | Team reports boards available; RP2040 is a candidate | Inventory exact models and choose development pair |
| Motor driver | L298N proposed, not finalized | Check voltage loss, motor current, braking, and current-limit support |
| UWB | Makerfabs STM32 AoA kit recommended; purchase unconfirmed | Check complete kit contents and run range/bearing bench experiment |
| IMU | ICM-20948 proposed; exact module unconfirmed | Select compatible breakout and log yaw during drive tests |
| ToF | Optional early stopping; module not finalized | Define sensing coverage and stop behavior before integration |
| Battery and regulator | Not selected | Establish nominal/max voltage, discharge current, energy/runtime, protection, and regulated logic supply |
| Joystick | Required manual-control capability; device not selected | Choose available controller and define command timeout |

## First work sessions

1. Inventory received hardware and resolve total mass versus payload assumption.
2. Record motor and encoder specifications, chassis dimensions, and prototype mass.
3. Define the Pi/MCU command and telemetry interface.
4. Run UWB bench validation independently of chassis bring-up.
5. Bring up manual driving, encoder feedback, watchdog stopping, and battery power.
6. Record baseline current, voltage sag, braking, and turning before following integration.

No hardware purchase, custom electronics, full-load performance, or implementation code is claimed complete.
