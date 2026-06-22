from config.pins import PINS
from control.drivers.pump import Pump
from control.drivers.relay import Relay
from control.drivers.rgb_sensor import RGBSensor


class Feeding:

    DEFAULT_TARGET_Density = 7000

    def __init__(
            self,
            target_density = DEFAULT_TARGET_Density,
            laser_relay = None,
            light_sensor = None,
            waste_pump = None
        ):

        self.target_density = float(target_density)

        self.laser_relay = laser_relay or Relay(
            "laser relay",
            PINS["laser"]["relay"]
        )

        self.light_sensor = light_sensor or RGBSensor(
            PINS["rgb"]["sda"],
            PINS["rgb"]["scl"],
            led_pin=PINS["laser"]["led"]
        )

        self.waste_pump = waste_pump or Pump(
            "waste pump",
            PINS["waste_pump"]["1"],
            PINS["waste_pump"]["2"],
        )

        self.enabled = True
        self.feeding = False

        self.current_density = None
        self.output_percent = 0.0

        self.off()

    def set_target(self, target_temp_c):
        self.target_density = float(target_temp_c)
        print("[feeding] target changed to:", self.target_density)
        return self.target_density

    def enable(self):
        self.enabled = True
        print("[feeding] enabled")

    def disable(self):
        self.enabled = False
        self.off()
        print("[feeding] disabled")

    def read_density(self):
        # Activate laser
        # Wait shortly
        density = self.light_sensor.read_raw()["green"]
        # Laser off
        if density is None:
            raise ValueError("OD sensor returned None")

        return float(density)

    def compute_output(self):
        # TODO: determine if/how long pump should pump
        return 0

    def step(self):
        if not self.enabled:
            self.off()
            return self.get_status()

        try:
            # TODO: New thread for waiting
            density = self.read_density()
            self.current_density = density

            output = self.compute_output()
            print("[feeding] density=", density, "target=", self.target_density, "output_percent=", output, "feeding=", self.feeding)

            if self._should_pump(density, output):
                self._pump_on()
            else:
                self._pump_off()

        except Exception as exc:
            print("thermal pid error:", exc)
            self.off()

        return self.get_status()

    def update(self=None):
        if self is None:
            return Feeding.default().step
        return self.step()

    def off(self):
        self._pump_off(force=True)
        self.output_percent = 0.0

    def _should_pump(self, temp_c, output_percent):
        if output_percent <= 0:
            return False

        if self.cooling:
            return temp_c > self.target_temp_c

        return temp_c > (self.target_temp_c + self.hysteresis_c)

    def _pump_on(self):
        if self.cooling:
            return

        print("[feeding] pump ON")
        self.waste_pump.on()
        self.feeding = True

    def _pump_off(self, force=False):
        if not self.cooling and not force:
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
            "target_density": self.target_density,
            "current_desity": self.current_density,
            "error": error,
            "output_percent": self.output_percent,
            "feeding": self.feeding,
        }