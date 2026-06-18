import os
from time import ticks_ms, ticks_diff

from config.features import FEATURES
from control.drivers.thermistor import init_temp_sensor, read_temp_details


class TemperatureControl:
    def __init__(
        self,
        csv_path="/data/temp_log.csv",
        interval_ms=1000,
        adc_pin=34,
        verbose=None,
        log_enabled=None
    ):
        self.csv_path = csv_path
        self.interval_ms = interval_ms
        self.adc_pin = adc_pin

        if verbose is None:
            verbose = FEATURES["print_temperature"]

        if log_enabled is None:
            log_enabled = FEATURES["log_temperature"]

        self.verbose = verbose
        self.log_enabled = log_enabled

        self.sensor = None
        self.enabled = False
        self.latest = None
        self.last_log_time = ticks_ms()

        if self.log_enabled:
            self._ensure_data_folder()
            self._reset_csv_file()

        self._setup_sensor()

    def _ensure_data_folder(self):
        try:
            os.mkdir("/data")
        except OSError:
            pass

    def _reset_csv_file(self):
        with open(self.csv_path, "w") as file:
            file.write("time_ms,temp_c,raw_average,voltage,resistance\n")

        print("Temperature CSV reset:", self.csv_path)

    def _setup_sensor(self):
        try:
            self.sensor = init_temp_sensor(self.adc_pin)
            self.enabled = True

            print("Temperature sensor enabled.")
            print("Thermistor ADC pin: GPIO", self.adc_pin)

            if self.log_enabled:
                print("Temperature CSV logging enabled:", self.csv_path)
            else:
                print("Temperature CSV logging disabled.")

        except Exception as error:
            print("Temperature setup failed:", error)

    def update(self):
        if not self.enabled:
            return self.latest

        now = ticks_ms()

        if ticks_diff(now, self.last_log_time) < self.interval_ms:
            return self.latest

        self.last_log_time = now

        try:
            details = read_temp_details(self.sensor)

            self.latest = {
                "time_ms": now,
                "temp_c": details["temp_c"],
                "raw_average": details["raw_average"],
                "voltage": details["voltage"],
                "resistance": details["resistance"]
            }

            if self.log_enabled:
                self._write_row(self.latest)

            if self.verbose:
                print(
                    "TEMP ->",
                    "{:.2f} C".format(self.latest["temp_c"]),
                    "raw:", "{:.1f}".format(self.latest["raw_average"]),
                    "V:", "{:.3f}".format(self.latest["voltage"]),
                    "R:", "{:.0f}".format(self.latest["resistance"])
                )

            return self.latest

        except Exception as error:
            print("Temperature read error:", error)
            return self.latest

    def _write_row(self, values):
        line = "{},{:.2f},{:.2f},{:.4f},{:.2f}".format(
            values["time_ms"],
            values["temp_c"],
            values["raw_average"],
            values["voltage"],
            values["resistance"]
        )

        with open(self.csv_path, "a") as file:
            file.write(line + "\n")

    def enable_logging(self):
        self.log_enabled = True
        self._ensure_data_folder()
        self._reset_csv_file()
        print("Temperature CSV logging enabled:", self.csv_path)

    def disable_logging(self):
        self.log_enabled = False
        print("Temperature CSV logging disabled.")

    def set_logging(self, enabled):
        if enabled:
            self.enable_logging()
        else:
            self.disable_logging()

    def get_latest(self):
        return self.latest


# Backwards-compatible alias if old code imports TempLogger.
TempLogger = TemperatureControl
