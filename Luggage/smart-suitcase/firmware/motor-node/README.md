# Motor controller node

MicroPython firmware for the low-level motor controller: a Raspberry Pi Pico H
driving an OSOYOO Model X (L298N) dual H-bridge.

This is a port of the OSOYOO smart-car lesson-1 sketch, restructured so the
closed-loop work described in [the MVP plan](../../docs/mvp-plan.md) §6 can be
added without a rewrite.

## Layers

| File | Responsibility |
|---|---|
| `board_config.py` | Pins, PWM frequency, calibration constants. The only file that knows the wiring. |
| `motor_driver.py` | One H-bridge channel. `set(duty)` where duty is −1.0…+1.0 and sign is direction. |
| `drive.py` | Differential layer. `tank(l, r)` plus named moves. |
| `main.py` | Serial command loop. |

Each layer only knows the one below it. A velocity controller attaches at
`main.control_tick()` and writes into `drive.tank()` — no other file changes.
Swapping the L298N for a MOSFET driver means one replacement for
`motor_driver.py`.

## Wiring

| Pico | Model X | Side |
|---|---|---|
| GP0 | ENA | right, PWM |
| GP1 | IN1 | right |
| GP2 | IN2 | right |
| GP3 | IN3 | left |
| GP4 | IN4 | left |
| GP5 | ENB | left, PWM |
| GND | GND | **required** — common ground or nothing works |

The right/left assignment follows OSOYOO's reference wiring (channel A is the
right motor). If your build is mirrored, swap `MOTOR_LEFT` and `MOTOR_RIGHT` in
`board_config.py`.

Three things to check before powering up:

- **Remove the ENA/ENB jumpers** if the board has them. They strap enable high
  and your PWM will do nothing.
- **Do not connect the Model X 5 V rail to the Pico.** The Pico is powered over
  USB; back-feeding VSYS from the module's regulator while USB is also connected
  is a bad time.
- **Pull the module's 5 V regulator jumper** if the motor supply is above 12 V.

## Install

Flash MicroPython once — hold BOOTSEL while plugging in the Pico, then drag the
`.uf2` from [micropython.org/download/RPI_PICO](https://micropython.org/download/RPI_PICO/)
onto the drive that appears.

Then:

```
pip install mpremote
mpremote cp board_config.py motor_driver.py drive.py :
```

Note `main.py` is **not** in that list. MicroPython auto-runs `main.py` at boot,
which would start the command loop and occupy the REPL. During bring-up you want
the REPL. Work from it instead:

```
mpremote
>>> from drive import Drive
>>> d = Drive()
>>> d.tank(0.5, 0.5)
>>> d.stop()
```

Copy `main.py` once the wiring is proven and you want the node to come up on its
own.

## Commands

Once `main.py` is running (`mpremote run main.py`, or on boot):

```
t <left> <right>   tank drive, each -1.0 to 1.0, positive forward
s                  stop (coast)
b                  brake
d                  run the lesson-1 demo sequence
w <0|1>            command-timeout watchdog off/on
?                  status
<blank line>       heartbeat
```

The watchdog stops the node if a `t` command isn't refreshed within
`CMD_TIMEOUT_MS` (500 ms default). That's intentional — it's how the interface
behaves once the Pi is driving, and a dead host must not leave the wheels
turning. For bench work where you want to set a speed and watch it, `w 0`.

The host is a USB serial port either way, so this is identical from your laptop
now (`COM*`, PuTTY or the VS Code serial monitor) and from the Pi later
(`/dev/ttyACM0`).

## Bring-up checklist

**Get the chassis on blocks first.** Wheels off the ground for everything below.

1. `d.tank(0.3, 0)` — `tank(left, right)`, so only the **left** wheel should
   turn, forward. If it runs backwards, set `invert: True` on `MOTOR_LEFT`. If
   the *right* wheel turned, swap the two descriptors.
2. Repeat with `d.tank(0, 0.3)` for the right side.
3. **Find each side's duty floors.** Zero that motor's `min_duty` and
   `kick_duty` first so they don't mask the raw behaviour, then ramp up until
   it turns (breakaway) and ramp back down until it stalls (sustain). Put
   sustain in `min_duty` and breakaway-plus-margin in `kick_duty`, per side.
   The L298N has a real deadband and the velocity loop will hunt forever
   without this.
4. **Check the heatsink.** Run `d.tank(0.6, 0.6)` for a minute and feel the
   module. 20 kHz is hard on a Darlington bridge. If it's too hot to hold, drop
   `PWM_FREQ_HZ` to 8000 and accept the audible whine.
5. `d.tank(0.5, 0.5)` then `d.tank(-0.5, -0.5)` — confirm the reversal dwell
   makes this a pause rather than a bang.

## Measured on this hardware

7.4 V bench supply, wheels unloaded on blocks. 2026-09-16.

Remember `tank(left, right)` — the **first** argument is the left motor
(channel B, ENB/IN3/IN4). Measurements were taken one side at a time with
`min_duty` and `kick_duty` temporarily zeroed so the raw floor was visible.

### PWM frequency, left motor

| PWM frequency | Breakaway duty |
|---|---|
| 20 kHz | 0.70 |
| 1 kHz | 0.50 |

**20 kHz is wrong for an L298N.** Darlington rise and storage times eat a
15 µs pulse, so little charge reaches the motor. `PWM_FREQ_HZ` is 1000 and
should not go back up without re-measuring both sides. The price is audible
whine, loud on an unloaded motor.

Current drawn while ramping the left motor at 1 kHz: rising with duty while
stalled (0.075 A → 0.20 A over duty 0.2 → 0.4), then flattening once turning
(0.20 A → 0.25 A over duty 0.5 → 0.7) as back-EMF opposes the supply.

### Duty floors, both sides at 1 kHz

| Side | Breakaway (from rest) | Sustain (already turning) |
|---|---|---|
| Left (channel B) | 0.50 | 0.20 |
| Right (channel A) | 0.40 | 0.15 |

Two things follow.

**Breakaway and sustain are far apart**, so `min_duty` alone isn't enough — a
command between the two would buzz without starting. That is what `kick_duty`
is for: a brief pulse just above breakaway, then a drop to the requested duty.
Verified working at `d.tank(0.25, 0)`, which previously only buzzed.

**The sides differ by ~25%.** Equal duty does not mean equal speed, so
open-loop straight driving will veer. Per-side floors (now in the motor
descriptors) reduce the effect but cannot remove it — only encoder feedback
will. Worth knowing before anyone tries to tune straightness by hand.

> **TODO — re-measure the asymmetry before trusting it.** The 0.50/0.40 split
> came from a single pass per side, 1.5 s per step, judged by eye, on a bench
> supply limited to 400 mA. Any of those could manufacture a difference that
> isn't really there:
>
> - Steps were 0.05 apart, so the true values could be within one step of each
>   other and still read as 0.50 vs 0.40.
> - One trial each. Static friction in a geared motor varies run to run
>   depending on where the gear teeth and brushes happen to be sitting.
> - The two motors were not necessarily mounted or loaded identically.
> - A 400 mA limit may have been clamping one side and not the other.
>
> Redo it with: the supply limit raised well clear (≥1.5 A), 0.02 steps, five
> trials per side alternating between them, and the wheel rotated to a
> different starting position each time. If the difference survives that, it
> is real and belongs to the motors. If it collapses, delete the per-side
> values and go back to one global figure.

### What this says about the driver

The L298N is the constraint behind all three of these findings. It cannot
switch fast enough to stay inaudible without losing low-duty output, it drops
~2 V, and it has no usable current sense on this module. A MOSFET driver
(TB6612FNG, DRV8871) would run at 20 kHz silently, shrink the deadband, and
give back the control range — the MVP plan's §4 note that "a suitable MOSFET
driver may be preferable" is now backed by measurement rather than suspicion.

`motor_driver.py` is deliberately the only file that touches the bridge, so a
swap is one replacement file and no changes above it.

## Known gaps

- **No current sensing.** The L298N has sense pins but this module almost
  certainly grounds them — check your board. If so there is no current limit and
  no inner current loop, contrary to the MVP plan §6. A fuse in the motor supply
  is the substitute. Stall detection needs encoders first.
- **~2 V bridge drop.** Motors see roughly 2 V less than the pack. Factor this
  into drivetrain sizing.
- **PWM keeps running after Ctrl-C.** On RP2040 the PWM peripheral can survive a
  script exiting, which leaves the wheels turning. `main.py` handles this in a
  `finally`, but if you're driving from the REPL and get stuck:

  ```
  >>> import motor_driver; motor_driver.emergency_stop()
  ```

- **The breakaway kick blocks.** `Motor.set()` sleeps for `KICK_MS` when
  starting from rest below `KICK_DUTY`, so a two-sided command stalls the
  caller for ~240 ms. Acceptable while the command loop only services a
  REPL-speed stream. Once a velocity loop runs on a fixed tick it will
  swallow several ticks and must be reworked as a state machine: record a
  deadline, return immediately, drop to the target duty on a later tick.
  Marked `TODO(non-blocking)` in `motor_driver.py`.
- Not implemented: encoders, velocity loop, telemetry, framed protocol,
  hardware watchdog. Hooks exist; no stubs pretending to work.
