try:
    from time import ticks_ms, ticks_diff
except ImportError:
    import time as _time

    _start = _time.monotonic()

    def ticks_ms():
        return int((_time.monotonic() - _start) * 1000)

    def ticks_diff(now, then):
        return now - then

from config.pins import PINS
from control.drivers.pump import Pump
from control.drivers.relay import Relay
from control.drivers.thermistor import Thermistor


class Thermal_PID:
    """
    - If temperature rises above target + hysteresis, cooling turns ON.
    - While cooling, cooling stays ON until temperature reaches target.
    - At or below target, cooling turns OFF.
    """

    DEFAULT_TARGET_TEMP_C = 13.0
    DEFAULT_HYSTERESIS_C = 0.75

    _default = None

    def __init__(
        self,
        target_temp_c=DEFAULT_TARGET_TEMP_C,
        hysteresis_c=DEFAULT_HYSTERESIS_C,
        kp=30.0, # proportional control
        ki=0.02, # integral control
        kd=0.0,  # derivative control
        temp_sensor=None,
        cooler_pump=None,
        peltier=None,
    ):
        self.target_temp_c = float(target_temp_c)
        self.hysteresis_c = float(hysteresis_c)

        self.kp = float(kp)
        self.ki = float(ki)
        self.kd = float(kd)

        self.temp_sensor = temp_sensor or Thermistor(
            name="thermal pid thermistor",
            adc_pin=PINS["temperature"]["adc"],
        )

        self.cooler_pump = cooler_pump or Pump(
            "cooler pump",
            PINS["cooler_pump"]["1"],
            PINS["cooler_pump"]["2"],
        )

        self.peltier = peltier or Relay(
            "peltier relay",
            PINS["peltier"]["relay"],
        )

        self.enabled = True
        self.cooling = False

        self.integral = 0.0
        self.integral_limit = 100.0
        self.last_error_c = None
        self.last_update_ms = None

        self.current_temp_c = None
        self.output_percent = 0.0
        self.last_error_msg = None

        self.off()
        print("[thermal_pid] initialized target=", self.target_temp_c, "hysteresis=", self.hysteresis_c, "kp=", self.kp, "ki=", self.ki, "kd=", self.kd)

    @classmethod
    def default(cls):
        if cls._default is None:
            cls._default = cls()
        return cls._default

    @classmethod
    def configure(cls, **kwargs):
        cls._default = cls(**kwargs)
        return cls._default

    @classmethod
    def set_target_temp(cls, target_temp_c):
        return cls.default().set_target(target_temp_c)

    @classmethod
    def status(cls):
        return cls.default().get_status()

    def set_target(self, target_temp_c):
        self.target_temp_c = float(target_temp_c)
        self.reset_pid()
        print("[thermal_pid] target changed to:", self.target_temp_c)
        return self.target_temp_c

    def set_pid(self, kp=None, ki=None, kd=None):
        if kp is not None:
            self.kp = float(kp)
        if ki is not None:
            self.ki = float(ki)
        if kd is not None:
            self.kd = float(kd)
        self.reset_pid()

    def set_hysteresis(self, hysteresis_c):
        self.hysteresis_c = float(hysteresis_c)

    def enable(self):
        self.enabled = True
        self.reset_pid()
        print("[thermal_pid] enabled")

    def disable(self):
        self.enabled = False
        self.off()
        print("[thermal_pid] disabled")

    def reset_pid(self):
        self.integral = 0.0
        self.last_error_c = None
        self.last_update_ms = None
        self.output_percent = 0.0

    def read_temperature(self):
        temp_c = self.temp_sensor.read_temp()
        if temp_c is None:
            raise ValueError("temperature sensor returned None")
        return float(temp_c)

    def compute_output(self, temp_c):
        # Positive error means the water is warmer than the target.
        now_ms = ticks_ms()
        error_c = float(temp_c) - self.target_temp_c

        if self.last_update_ms is None:
            dt_s = 0.0
        else:
            dt_s = ticks_diff(now_ms, self.last_update_ms) / 1000.0
            if dt_s < 0:
                dt_s = 0.0

        if error_c <= 0:
            self.integral = 0.0
            derivative = 0.0
        else:
            if dt_s > 0:
                self.integral += error_c * dt_s

                if self.integral > self.integral_limit:
                    self.integral = self.integral_limit
                elif self.integral < -self.integral_limit:
                    self.integral = -self.integral_limit

            if self.last_error_c is None or dt_s <= 0:
                derivative = 0.0
            else:
                derivative = (error_c - self.last_error_c) / dt_s

        output = (self.kp * error_c) + (self.ki * self.integral) + (self.kd * derivative)

        if output < 0:
            output = 0.0
        elif output > 100.0:
            output = 100.0

        self.last_error_c = error_c
        self.last_update_ms = now_ms
        self.output_percent = output

        return output

    def step(self):
        if not self.enabled:
            self.off()
            return self.get_status()

        try:
            temp_c = self.read_temperature()
            self.current_temp_c = temp_c
            self.last_error_msg = None

            output = self.compute_output(temp_c)
            print("[thermal_pid] temp_c=", temp_c, "target=", self.target_temp_c, "output_percent=", output, "cooling=", self.cooling)

            if self._should_cool(temp_c, output):
                self._cooling_on()
            else:
                self._cooling_off()

        except Exception as exc:
            self.last_error_msg = str(exc)
            print("thermal pid error:", self.last_error_msg)
            self.off()

        return self.get_status()

    def update(self=None):
        if self is None:
            return Thermal_PID.default().step
        return self.step()

    def off(self):
        self._cooling_off(force=True)
        self.output_percent = 0.0
        self.reset_pid()

    def _should_cool(self, temp_c, output_percent):
        if output_percent <= 0:
            return False

        if self.cooling:
            return temp_c > self.target_temp_c

        return temp_c > (self.target_temp_c + self.hysteresis_c)

    def _cooling_on(self):
        if self.cooling:
            return

        print("[thermal_pid] cooling ON")
        self.cooler_pump.on()
        self.peltier.on()
        self.cooling = True

    def _cooling_off(self, force=False):
        if not self.cooling and not force:
            return

        print("[thermal_pid] cooling OFF")
        self.peltier.off()
        self.cooler_pump.off()
        self.cooling = False

    def get_status(self):
        error_c = None
        if self.current_temp_c is not None:
            error_c = self.current_temp_c - self.target_temp_c

        return {
            "enabled": self.enabled,
            "target_temp_c": self.target_temp_c,
            "hysteresis_c": self.hysteresis_c,
            "current_temp_c": self.current_temp_c,
            "error_c": error_c,
            "output_percent": self.output_percent,
            "cooling": self.cooling,
            "last_error_msg": self.last_error_msg,
        }