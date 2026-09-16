"""Command loop for the smart-suitcase motor controller node.

Boots to a stopped state and waits. Nothing moves until you ask it to.

Commands (one per line, over the USB serial port):

    t <left> <right>   tank drive, each -1.0 .. 1.0, positive is forward
    s                  stop (coast)
    b                  brake
    d                  run the Arduino lesson demo sequence
    w <0|1>            command-timeout watchdog off/on
    ?                  status
    <blank line>       heartbeat -- refreshes the watchdog, changes nothing

While the watchdog is on, a `t` command expires after
board_config.CMD_TIMEOUT_MS and the node stops itself. That is deliberate:
it is how the real interface will behave once the Pi is driving, and it
means a dead host cannot leave the wheels running. For bench work where
you want to set a speed and watch it, turn it off with `w 0`.

The loop is deliberately non-blocking -- no sleep chains, no long-running
calls -- so that a control loop can be added at control_tick() without
restructuring anything.
"""

import select
import sys
import time

import board_config as cfg
import motor_driver
from drive import DEMO_SEQUENCE, Drive

BANNER = """
smart-suitcase motor node
  t <l> <r> | s | b | d | w <0|1> | ?
  stopped. nothing moves until commanded.
"""


def control_tick(drive, dt_ms):
    """Called every loop iteration at roughly board_config.TICK_HZ.

    Empty on purpose. This is where the velocity loop lands: read encoder
    deltas, compare against a target, and write the result into
    drive.tank(). Nothing else in this file needs to change when it does.
    """
    return


class Node:
    def __init__(self, drive=None):
        self.drive = drive if drive is not None else Drive()
        self.watchdog = cfg.CMD_TIMEOUT_MS > 0

        self._last_cmd_ms = time.ticks_ms()
        self._demo_step = None
        self._demo_deadline = 0
        self._buf = ""

        self._poll = select.poll()
        self._poll.register(sys.stdin, select.POLLIN)

    # -- input ------------------------------------------------------------

    def _pump_stdin(self):
        """Drain whatever characters are waiting. Never blocks."""
        while self._poll.poll(0):
            ch = sys.stdin.read(1)
            if not ch:
                return
            if ch in ("\r", "\n"):
                line, self._buf = self._buf, ""
                self._handle(line)
            elif ch in ("\x7f", "\x08"):
                self._buf = self._buf[:-1]
            else:
                self._buf += ch
                if len(self._buf) > 64:
                    self._buf = ""
                    print("! line too long, discarded")

    def _handle(self, line):
        parts = line.strip().split()
        if not parts:
            self._last_cmd_ms = time.ticks_ms()  # bare newline: heartbeat
            return

        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd == "t":
                left, right = float(args[0]), float(args[1])
                self._demo_step = None
                self.drive.tank(left, right)
                print("ok t %.2f %.2f" % self.drive.duty)

            elif cmd == "s":
                self._demo_step = None
                self.drive.stop()
                print("ok stop")

            elif cmd == "b":
                self._demo_step = None
                self.drive.brake()
                print("ok brake")

            elif cmd == "d":
                self._start_demo()

            elif cmd == "w":
                self.watchdog = bool(int(args[0]))
                print("ok watchdog %s" % ("on" if self.watchdog else "OFF"))

            elif cmd in ("?", "h", "help"):
                self._status()

            else:
                print("! unknown command %r" % cmd)

        except (IndexError, ValueError):
            print("! bad arguments for %r" % cmd)

        finally:
            # Stamped after dispatch, not before. A breakaway kick blocks for
            # cfg.KICK_MS per motor, so a two-sided command can burn ~240 ms
            # of a 500 ms watchdog window before the wheels are even up to
            # speed. Measuring the timeout from when the command finished
            # keeps that from counting against the host.
            self._last_cmd_ms = time.ticks_ms()

    def _status(self):
        left, right = self.drive.duty
        print(
            "duty L=%+.2f R=%+.2f | moving=%s | watchdog=%s (%d ms) | "
            "demo=%s | pwm=%d Hz | min_duty=%.2f"
            % (
                left,
                right,
                self.drive.moving,
                "on" if self.watchdog else "off",
                cfg.CMD_TIMEOUT_MS,
                "step %d" % self._demo_step if self._demo_step is not None else "idle",
                cfg.PWM_FREQ_HZ,
                cfg.MIN_DUTY,
            )
        )

    # -- demo -------------------------------------------------------------

    def _start_demo(self):
        self._demo_step = 0
        self._apply_demo_step()

    def _apply_demo_step(self):
        name, duration_ms = DEMO_SEQUENCE[self._demo_step]
        getattr(self.drive, name)()
        self._demo_deadline = time.ticks_add(time.ticks_ms(), duration_ms)
        print("demo: %s (%d ms)" % (name, duration_ms))

    def _service_demo(self, now):
        if self._demo_step is None:
            return
        if time.ticks_diff(now, self._demo_deadline) < 0:
            return

        self._demo_step += 1
        if self._demo_step >= len(DEMO_SEQUENCE):
            self._demo_step = None
            self.drive.stop()
            print("demo: done")
        else:
            self._apply_demo_step()

    # -- safety -----------------------------------------------------------

    def _service_watchdog(self, now):
        if not self.watchdog or self._demo_step is not None:
            return
        if not self.drive.moving:
            return
        if time.ticks_diff(now, self._last_cmd_ms) > cfg.CMD_TIMEOUT_MS:
            self.drive.stop()
            print("! command timeout -- stopped")

    # -- loop -------------------------------------------------------------

    def run(self):
        period_ms = 1000 // cfg.TICK_HZ
        self.drive.stop()
        print(BANNER)

        last = time.ticks_ms()
        try:
            while True:
                now = time.ticks_ms()

                self._pump_stdin()
                self._service_demo(now)
                self._service_watchdog(now)
                control_tick(self.drive, time.ticks_diff(now, last))

                last = now
                time.sleep_ms(period_ms)

        except KeyboardInterrupt:
            print("\ninterrupted")
        finally:
            # Belt and braces: emergency_stop() touches the pins directly
            # rather than going through the objects, so it still works if
            # the Drive got into a strange state.
            motor_driver.emergency_stop()
            print("motors safe")


def run():
    Node().run()


if __name__ == "__main__":
    run()
