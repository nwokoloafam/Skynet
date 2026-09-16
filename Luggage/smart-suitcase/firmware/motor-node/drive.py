"""Differential drive layer.

Turns whole-robot intent into per-side duty. `tank()` is the real API and
the single place anything is commanded -- every named move below routes
through it, and a velocity controller added later writes into it too. If
you are looking for where to attach closed-loop control, it is here.

Sides are LEFT and RIGHT regardless of which H-bridge channel they sit on;
board_config owns that mapping.
"""

import board_config as cfg
from motor_driver import Motor

# The Arduino lesson's sequence, as (method name, duration in ms).
# Advanced by the caller so it stays interruptible -- see main.run().
DEMO_SEQUENCE = (
    ("forward", 2000),
    ("reverse", 2000),
    ("spin_left", 2000),
    ("spin_right", 2000),
    ("stop", 0),
)


class Drive:
    """Two motors commanded as a differential pair."""

    def __init__(self, left=None, right=None):
        self.left = left if left is not None else Motor(**cfg.MOTOR_LEFT)
        self.right = right if right is not None else Motor(**cfg.MOTOR_RIGHT)

    # -- primary API ------------------------------------------------------

    def tank(self, left, right):
        """Command each side directly, -1.0 .. +1.0. Positive is forward."""
        self.left.set(left)
        self.right.set(right)

    def arcade(self, forward, yaw):
        """Command forward effort and yaw effort, each -1.0 .. +1.0.

        Positive yaw turns left, matching the MVP plan's convention
        (v_left = v - yaw, v_right = v + yaw). If the combination would
        exceed full scale, both sides are scaled down together so the
        turn ratio survives.
        """
        left = forward - yaw
        right = forward + yaw

        peak = max(abs(left), abs(right))
        if peak > 1.0:
            left /= peak
            right /= peak

        self.tank(left, right)

    # -- named moves, matching the Arduino lesson -------------------------

    def forward(self, speed=None):
        speed = cfg.DEMO_DUTY if speed is None else speed
        self.tank(speed, speed)

    def reverse(self, speed=None):
        speed = cfg.DEMO_DUTY if speed is None else speed
        self.tank(-speed, -speed)

    def spin_left(self, speed=None):
        """Rotate counter-clockwise in place: left side back, right forward."""
        speed = cfg.DEMO_DUTY if speed is None else speed
        self.tank(-speed, speed)

    def spin_right(self, speed=None):
        """Rotate clockwise in place: left side forward, right back."""
        speed = cfg.DEMO_DUTY if speed is None else speed
        self.tank(speed, -speed)

    # -- stopping ---------------------------------------------------------

    def stop(self):
        """Coast to a halt. This is the safe default state."""
        self.left.coast()
        self.right.coast()

    def brake(self):
        """Short both motors. Stops quickly; harder on the drivetrain."""
        self.left.brake()
        self.right.brake()

    # -- state ------------------------------------------------------------

    @property
    def moving(self):
        return self.left.moving or self.right.moving

    @property
    def duty(self):
        """Current (left, right) duty as last commanded."""
        return (self.left.duty, self.right.duty)

    def deinit(self):
        self.left.deinit()
        self.right.deinit()
