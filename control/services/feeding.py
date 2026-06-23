from config.pins import PINS
from control.drivers.pump import Pump
from control.drivers.relay import Relay
from control.drivers.rgb_sensor import RGBSensor

import time
import _thread


class Feeding:

    DEFAULT_TARGET_DENSITY = 7000
    LASER_WAIT_MS = 200
    DENSITY_DROP_PER_SECOND = 2000
    MAX_PUMP_MS = 10000

    def __init__(
            self,
            target_density=DEFAULT_TARGET_DENSITY,
            laser_relay=None,
            light_sensor=None,
            waste_pump=None
        ):

        self.target_density = float(target_density)

        self.laser_relay = laser_relay or Relay(
            "laser relay",
            PINS["laser"]["relay"]
        )

        self.light_sensor = light_sensor or RGBSensor(
            PINS["rgb"]["sda"],
            PINS["rgb"]["scl"],
            led_pin=PINS["rgb"]["led"]
        )

        self.waste_pump = waste_pump or Pump(
            "waste pump",
            PINS["waste_pump"]["1"],
            PINS["waste_pump"]["2"],
        )

        self.enabled = True
        self.feeding = False
        self.busy = False

        self.current_density = None
        self.output_percent = 0.0
        self.pump_ms = 0

        self._lock = _thread.allocate_lock()

        self.off()

    def set_target(self, target_density):
        self.target_density = float(target_density)
        print("[feeding] target changed to:", self.target_density)

    def enable(self):
        self.enabled = True
        print("[feeding] enabled")

    def disable(self):
        self.enabled = False
        self.off()
        print("[feeding] disabled")

    def read_density(self):
        self.laser_relay.on()
        time.sleep_ms(self.LASER_WAIT_MS)

        light_reading = self.light_sensor.read_raw()["green"]

        self.laser_relay.off()

        if light_reading is None:
            raise ValueError("OD sensor returned None")

        density = self.light_to_density(light_reading)
        density = 5000  # Temporary test value
        return float(density)

    def light_to_density(self, light_reading):
        # TODO: Eventually use calibration
        return light_reading

    def compute_output(self, density):
        error = density - self.target_density

        if error <= 0:
            return 0

        pump_ms = int((error / self.DENSITY_DROP_PER_SECOND) * 1000)

        if pump_ms > self.MAX_PUMP_MS:
            pump_ms = self.MAX_PUMP_MS

        return pump_ms

    def step(self):
        if not self.enabled:
            self.off()
            return

        with self._lock:
            if self.busy:
                return
            self.busy = True

        _thread.start_new_thread(self._feeding_cycle, ())

    def _feeding_cycle(self):
        try:
            density = self.read_density()
            pump_ms = self.compute_output(density)

            self.current_density = density
            self.pump_ms = pump_ms
            self.output_percent = pump_ms

            print(
                "[feeding] density=",
                density,
                "target=",
                self.target_density,
                "pump_ms=",
                pump_ms
            )

            if pump_ms > 0 and self.enabled:
                self._pump_on()
                time.sleep_ms(pump_ms)
                self._pump_off()

        except Exception as exc:
            print("[feeding] error:", exc)
            self.off()

        finally:
            with self._lock:
                self.busy = False

    def update(self):
        self.step()

    def off(self):
        self._pump_off(force=True)
        self.output_percent = 0.0
        self.pump_ms = 0

    def _pump_on(self):
        if self.feeding:
            return

        print("[feeding] pump ON")
        self.waste_pump.on()
        self.feeding = True

    def _pump_off(self, force=False):
        if not self.feeding and not force:
            return

        print("[feeding] pump OFF")
        self.waste_pump.off()
        self.feeding = False

    def get_status(self):
        error = None
        if self.current_density is not None:
            error = self.current_density - self.target_density

        return {
            "enabled": self.enabled,
            "busy": self.busy,
            "target_density": self.target_density,
            "current_density": self.current_density,
            "error": error,
            "pump_ms": self.pump_ms,
            "feeding": self.feeding,
        }