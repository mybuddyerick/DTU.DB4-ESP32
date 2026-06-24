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
    - Peltier turns ON when temperature error > peltier_hysteresis_c (0.3°C)
    - Pump turns ON when temperature error > hysteresis_c (0.5°C)
    - Everything turns OFF when temperature drops back to or below target.
    """

    DEFAULT_TARGET_TEMP_C = 18
    PELTIER_ON_PERCENT = 15.0  # Peltier turns on when PID output hits 15%
    PUMP_ON_PERCENT = 20.0  # Pump turns on when PID output hits 30%
    OUTPUT_HYSTERESIS = 5.0  # 5% buffer to prevent chattering

    _default = None

    def __init__(
            self,
            target_temp_c=DEFAULT_TARGET_TEMP_C,
            kp=30.0,
            ki=0.02,
            kd=0.0,
            temp_sensor=None,
            cooler_pump=None,
            peltier=None,
    ):
        self.target_temp_c = float(target_temp_c)

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

        # Cleaned up state variables
        self.cooler_pump_running = False
        self.peltier_running = False

        self.off()
        print(
            "[thermal_pid] initialized target=", self.target_temp_c,
            "kp=", self.kp,
            "ki=", self.ki,
            "kd=", self.kd
        )

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

        if output < -100.0:
            output = -100.0
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

            # Calculate the PID output percentage (-100 to 100)
            output = self.compute_output(temp_c)

            # Master Kill Switch: If we are at/below target temperature
            if temp_c <= self.target_temp_c or output <= 0:
                self.peltier.off()
                self.cooler_pump.off()
                self.peltier_running = False
                self.cooler_pump_running = False
                self.cooling = False
            else:
                self.cooling = True

                # --- Peltier Control Logic with Percentage Hysteresis ---
                if self.peltier_running:
                    # Turn off only if output drops below threshold minus hysteresis
                    if output < (self.PELTIER_ON_PERCENT - self.OUTPUT_HYSTERESIS):
                        self.peltier.off()
                        self.peltier_running = False
                else:
                    # Turn on if output exceeds threshold
                    if output >= self.PELTIER_ON_PERCENT:
                        self.peltier.on()
                        self.peltier_running = True

                # --- Pump Control Logic with Percentage Hysteresis ---
                if self.cooler_pump_running:
                    # Turn off only if output drops below threshold minus hysteresis
                    if output < (self.PUMP_ON_PERCENT - self.OUTPUT_HYSTERESIS):
                        self.cooler_pump.off()
                        self.cooler_pump_running = False
                else:
                    # Turn on if output exceeds threshold
                    if output >= self.PUMP_ON_PERCENT:
                        self.cooler_pump.on()
                        self.cooler_pump_running = True

            print(
                "[thermal_pid] temp_c=", temp_c,
                "output_percent=", output,
                "peltier=", self.peltier_running,
                "pump=", self.cooler_pump_running
            )

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
        self.peltier.off()
        self.cooler_pump.off()
        self.peltier_running = False
        self.cooler_pump_running = False
        self.cooling = False
        self.output_percent = 0.0
        self.reset_pid()

    def get_status(self):
        error_c = None
        if self.current_temp_c is not None:
            error_c = self.current_temp_c - self.target_temp_c

        return {
            "enabled": self.enabled,
            "target_temp_c": self.target_temp_c,
            "current_temp_c": self.current_temp_c,
            "error_c": error_c,
            "output_percent": self.output_percent,
            "cooling": self.cooling,
            "peltier_running": self.peltier_running,
            "cooler_pump_running": self.cooler_pump_running,
            "last_error_msg": self.last_error_msg,
        }