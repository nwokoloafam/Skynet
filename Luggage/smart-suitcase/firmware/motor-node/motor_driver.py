"""Low-level motor driver -- the hardware abstraction layer.

One `Motor` object owns one H-bridge channel: an enable pin carrying PWM
and two direction pins. Duty is a signed float in -1.0 .. +1.0 where the
sign is the direction. Nothing above this module touches a pin.

This is sign-magnitude drive: the enable pin is modulated and the
direction pins are static. The alternative (locked antiphase) linearises
better around zero but roughly doubles L298N dissipation, which this part
cannot spare.

Swapping to a different driver board (TB6612, DRV8871, ...) means writing
a replacement for this file with the same four methods. Nothing above
changes.
"""

import time

from machine import PWM, Pin

import board_config as cfg


def _clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


class Motor:
    """A single H-bridge channel.

    Args:
        en:     GP number of the enable pin (gets PWM).
        in_a:   GP number of the first direction pin.
        in_b:   GP number of the second direction pin.
        invert: if True, positive duty drives the motor the other way.
        freq:   PWM frequency in Hz; defaults to board_config.PWM_FREQ_HZ.
    """

    def __init__(self, en, in_a, in_b, invert=False, freq=None,
                 min_duty=None, kick_duty=None, kick_ms=None):
        self._pwm = PWM(Pin(en))
        self._pwm.freq(freq if freq is not None else cfg.PWM_FREQ_HZ)
        self._pwm.duty_u16(0)

        self._a = Pin(in_a, Pin.OUT, value=0)
        self._b = Pin(in_b, Pin.OUT, value=0)

        self._invert = invert
        self._duty = 0.0  # last *requested* duty, pre-inversion

        # Per-side calibration. The two motors differ by ~25% in breakaway,
        # so a single global figure makes one side sluggish or the other
        # jumpy. These are plain attributes: tweak them live at the REPL
        # (m.min_duty = 0.1) while measuring, then write the result into
        # the descriptor in board_config.
        self.min_duty = cfg.MIN_DUTY if min_duty is None else min_duty
        self.kick_duty = cfg.KICK_DUTY if kick_duty is None else kick_duty
        self.kick_ms = cfg.KICK_MS if kick_ms is None else kick_ms

    # -- state ------------------------------------------------------------

    @property
    def duty(self):
        """Last requested duty, -1.0 .. +1.0. Sign is direction."""
        return self._duty

    @property
    def moving(self):
        return self._duty != 0.0

    # -- commands ---------------------------------------------------------

    def set(self, duty):
        """Drive at `duty` (-1.0 .. +1.0). Sign selects direction.

        A direction reversal while the motor is turning releases the bridge
        and dwells before re-engaging, so back-EMF is not slammed into the
        output transistors.

        Starting from rest, a command below the breakaway threshold gets a
        brief kick at cfg.KICK_DUTY first -- static friction in a geared
        motor is much higher than the duty needed to keep it turning.
        """
        duty = _clamp(float(duty), -cfg.MAX_DUTY, cfg.MAX_DUTY)

        # Raise sub-threshold commands to this side's duty floor. Commands
        # of exactly zero stay zero.
        if duty != 0.0 and self.min_duty > 0.0:
            if -self.min_duty < duty < self.min_duty:
                duty = self.min_duty if duty > 0 else -self.min_duty

        reversing = (
            duty != 0.0
            and self._duty != 0.0
            and (duty > 0.0) != (self._duty > 0.0)
        )
        if reversing:
            self._write(0.0)
            time.sleep_ms(cfg.REVERSE_DWELL_MS)

        # A reversal has just brought the motor to a stop, so it needs the
        # kick as much as a cold start does.
        from_rest = reversing or self._duty == 0.0
        if self._needs_kick(duty, from_rest):
            self._write(self.kick_duty if duty > 0.0 else -self.kick_duty)
            # TODO(non-blocking): this sleep stalls the caller for kick_ms.
            # Harmless while main.py is only servicing a REPL-speed command
            # stream, but once a velocity loop runs at a fixed tick it will
            # swallow several ticks. Rework as a state machine: record a
            # kick_until timestamp, return immediately, and let the tick
            # drop to the target duty once the deadline passes.
            time.sleep_ms(self.kick_ms)

        self._write(duty)
        self._duty = duty

    def _needs_kick(self, duty, from_rest):
        if not from_rest or duty == 0.0:
            return False
        if self.kick_duty <= 0.0:
            return False
        magnitude = duty if duty > 0.0 else -duty
        return magnitude < self.kick_duty

    def coast(self):
        """Release the bridge. Outputs go high-impedance; the motor freewheels."""
        self._write(0.0)
        self._duty = 0.0

    def brake(self):
        """Short the motor terminals together. Stops far faster than coasting.

        Both direction pins low with the enable pin held high turns on both
        low-side transistors, which shorts the winding through ground.
        """
        self._a.value(0)
        self._b.value(0)
        self._pwm.duty_u16(65535)
        self._duty = 0.0

    def deinit(self):
        """Release the PWM hardware. Call before re-importing at the REPL."""
        self.coast()
        self._pwm.deinit()

    # -- internals --------------------------------------------------------

    def _write(self, duty):
        out = -duty if self._invert else duty

        if out > 0.0:
            self._a.value(1)
            self._b.value(0)
        elif out < 0.0:
            self._a.value(0)
            self._b.value(1)
        else:
            # Both low + zero enable == coast.
            self._a.value(0)
            self._b.value(0)

        magnitude = out if out >= 0.0 else -out
        self._pwm.duty_u16(int(magnitude * 65535))


def emergency_stop():
    """Force every driver pin to a safe, coasting state.

    Deliberately takes no arguments and needs no existing object, so it
    works from a bare REPL. This matters: on RP2040 a PWM peripheral can
    keep running after Ctrl-C drops you out of a script, which leaves the
    wheels turning with nothing driving them. If that happens, type:

        import motor_driver; motor_driver.emergency_stop()
    """
    for pin in (cfg.PIN_ENA, cfg.PIN_ENB):
        try:
            pwm = PWM(Pin(pin))
            pwm.duty_u16(0)
            pwm.deinit()
        except Exception:
            pass
        Pin(pin, Pin.OUT, value=0)

    for pin in (cfg.PIN_IN1, cfg.PIN_IN2, cfg.PIN_IN3, cfg.PIN_IN4):
        Pin(pin, Pin.OUT, value=0)
