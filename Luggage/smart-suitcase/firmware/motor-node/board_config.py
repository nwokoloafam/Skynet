"""Hardware configuration for the smart-suitcase motor controller node.

This is the ONLY module that knows how the board is physically wired.
Nothing above it should contain a pin number, a frequency, or a
calibration constant. If you rewire, change it here and nowhere else.

Target: Raspberry Pi Pico H (RP2040) driving an OSOYOO Model X
(L298N dual H-bridge) module.
"""

# ---------------------------------------------------------------------------
# Pin map -- Pico GP numbers
# ---------------------------------------------------------------------------
# NOTE on sides: the OSOYOO reference wiring puts the RIGHT motor on
# channel A (ENA/IN1/IN2) and the LEFT motor on channel B (ENB/IN3/IN4).
# That convention is preserved here. If your build is mirrored, swap the
# two descriptors at the bottom of this file rather than editing pins.

PIN_ENA = 0   # PWM  -- channel A enable  (right side)
PIN_IN1 = 1   # GPIO -- channel A direction
PIN_IN2 = 2   # GPIO -- channel A direction
PIN_IN3 = 3   # GPIO -- channel B direction
PIN_IN4 = 4   # GPIO -- channel B direction
PIN_ENB = 5   # PWM  -- channel B enable  (left side)

# GP0 lands on PWM slice 0 channel A, GP5 on slice 2 channel B. Different
# slices, so the two sides carry independent duty AND independent frequency.
# GP1..GP4 are plain GPIO, so their slice assignments are irrelevant.

# ---------------------------------------------------------------------------
# PWM
# ---------------------------------------------------------------------------
# MEASURED 2026-09-16, 7.4 V supply, wheels unloaded on blocks.
#
# 20 kHz was tried first and is wrong for this part. The L298N's Darlington
# outputs have rise and storage times measured in microseconds, so at 20 kHz
# (50 us period) most of a short on-pulse is lost and almost no charge
# reaches the motor. Observed breakaway duty on the left motor was 0.70 at
# 20 kHz and 0.50 at 1 kHz. The cost of 1 kHz is an audible whine. Do not
# raise this back to 20 kHz without re-measuring both duty floors.
PWM_FREQ_HZ = 1000

# Hard ceiling on commanded duty. Lower it to derate the driver.
MAX_DUTY = 1.0

# ---------------------------------------------------------------------------
# Duty floors and breakaway kick
# ---------------------------------------------------------------------------
# Below some duty the bridge produces no useful torque and the motor just
# sits and buzzes. Two different numbers matter and they are far apart:
#
#   side    breakaway (from rest)   sustain (already turning)
#   left           0.50                     0.20
#   right          0.40                     0.15
#
# min_duty is set per side to the SUSTAIN figure, so slow commands work while
# the wheel is already moving. A command below the breakaway figure issued
# from rest would buzz without starting, which is what kick_duty exists to
# prevent: it briefly applies kick_duty (sized just above breakaway) to break
# static friction, then drops to the requested value.
#
# The two sides differ by ~25%. That asymmetry means equal duty does NOT mean
# equal speed, so open-loop straight driving will veer. Per-side floors reduce
# the effect but do not remove it -- only encoder feedback will.
#
# The values below are the defaults for any motor descriptor that does not
# override them. Both descriptors currently do override, so these only apply
# to motors constructed by hand.
MIN_DUTY = 0.20
KICK_DUTY = 0.55
KICK_MS = 120

# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------
# The Arduino lesson used analogWrite(..., 200), i.e. 200/255.
DEMO_DUTY = 0.78

# Time spent coasting between a forward command and a reverse command.
# Flipping the direction pins while the motor is still spinning under power
# dumps back-EMF into the bridge. The original sketch does exactly that.
REVERSE_DWELL_MS = 30

# ---------------------------------------------------------------------------
# Command loop
# ---------------------------------------------------------------------------
# If the node is moving and no command arrives within this window, it stops
# on its own. This is the first real safety primitive -- the Pi crashing
# must not leave the wheels running. Set to 0 to disable (bench use only).
CMD_TIMEOUT_MS = 500

# Main loop rate. Also the rate at which control_tick() is called.
TICK_HZ = 50

# ---------------------------------------------------------------------------
# Motor descriptors
# ---------------------------------------------------------------------------
# `invert` flips the meaning of positive duty for that side. Use it when a
# motor is wired backwards instead of swapping the physical leads.

# Measured 2026-09-16 -- see the duty floor section above for method.

MOTOR_RIGHT = {
    "en": PIN_ENA,
    "in_a": PIN_IN1,
    "in_b": PIN_IN2,
    "invert": False,
    "min_duty": 0.15,   # sustain
    "kick_duty": 0.45,  # just above the 0.40 breakaway
}

MOTOR_LEFT = {
    "en": PIN_ENB,
    "in_a": PIN_IN3,
    "in_b": PIN_IN4,
    "invert": False,
    "min_duty": 0.20,   # sustain
    "kick_duty": 0.55,  # just above the 0.50 breakaway
}
