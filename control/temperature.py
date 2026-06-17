import os
from time import ticks_ms, ticks_diff

from control.drivers.thermistor_driver import init_temp_sensor, read_temp_details


class TemperatureControl:
    def __init__(
        self,
        csv_path="/data/temp_log.csv",
        interval_ms=1000,
        adc_pin=34,
        verbose=True
    ):
        self.csv_path = csv_path
        self.interval_ms = interval_ms
        self.adc_pin = adc_pin
        self.verbose = verbose

        self.sensor = None
        self.enabled = False
        self.latest = None
        self.last_log_time = ticks_ms()

        self._ensure_data_folder()
        self._ensure_csv_header()
        self._setup_sensor()

    def _ensure_data_folder(self):
        try:
            os.mkdir("/data")
        except OSError:
            pass

    def _ensure_csv_header(self):
        needs_header = False

        try:
            size = os.stat(self.csv_path)[6]
            if size == 0:
                needs_header = True
        except OSError:
            needs_header = True

        if needs_header:
            with open(self.csv_path, "w") as file:
                file.write("time_ms,temp_c,raw_average,voltage,resistance")

    def _setup_sensor(self):
        try:
            self.sensor = init_temp_sensor(self.adc_pin)
            self.enabled = True

            print("Temperature logger enabled:", self.csv_path)
            print("Thermistor ADC pin: GPIO", self.adc_pin)

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
            file.write(line)

    def get_latest(self):
        return self.latest


# Backwards-compatible alias if old code imports TempLogger.
TempLogger = TemperatureControl
