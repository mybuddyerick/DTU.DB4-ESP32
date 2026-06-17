import os
from time import ticks_ms, ticks_diff

from control.drivers.tcs34725 import TCS34725


class RGBSensorControl:
    def __init__(
        self,
        csv_path="/data/rgb_log.csv",
        interval_ms=1000,
        sda_pin=21,
        scl_pin=22,
        led_pin=23,
        verbose=True
    ):
        self.csv_path = csv_path
        self.interval_ms = interval_ms
        self.verbose = verbose

        self.sensor = None
        self.enabled = False
        self.latest = None
        self.last_log_time = ticks_ms()

        self._ensure_data_folder()
        self._ensure_csv_header()
        self._setup_sensor(sda_pin, scl_pin, led_pin)

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
                file.write("time_ms,clear,red,green,blue")

    def _setup_sensor(self, sda_pin, scl_pin, led_pin):
        try:
            self.sensor = TCS34725(
                sda_pin=sda_pin,
                scl_pin=scl_pin,
                freq=50000,
                led_pin=led_pin
            )

            self.sensor.led_off()

            devices = self.sensor.scan()
            print("RGB I2C devices:", [hex(device) for device in devices])

            if not self.sensor.found():
                print("TCS34725 not found. RGB disabled.")
                return

            print("TCS34725 found. Sensor ID:", hex(self.sensor.sensor_id()))

            self.sensor.init()
            self.sensor.led_off()

            self.enabled = True
            print("RGB logger enabled:", self.csv_path)

        except Exception as error:
            print("RGB setup failed:", error)

    def update(self):
        if not self.enabled:
            return self.latest

        now = ticks_ms()

        if ticks_diff(now, self.last_log_time) < self.interval_ms:
            return self.latest

        self.last_log_time = now

        try:
            self.sensor.led_off()
            values = self.sensor.read_raw()

            if values is None:
                return self.latest

            self.latest = {
                "time_ms": now,
                "clear": values["clear"],
                "red": values["red"],
                "green": values["green"],
                "blue": values["blue"]
            }

            self._write_row(self.latest)

            if self.verbose:
                print(
                    "RGB ->",
                    "C:", self.latest["clear"],
                    "R:", self.latest["red"],
                    "G:", self.latest["green"],
                    "B:", self.latest["blue"]
                )

            return self.latest

        except OSError as error:
            print("RGB read error:", error)
            self._recover()
            return self.latest

    def _write_row(self, values):
        line = "{},{},{},{},{}".format(
            values["time_ms"],
            values["clear"],
            values["red"],
            values["green"],
            values["blue"]
        )

        with open(self.csv_path, "a") as file:
            file.write(line)

    def _recover(self):
        try:
            self.sensor.init()
            self.sensor.led_off()
            print("RGB recovered.")
        except Exception as error:
            print("RGB recovery failed:", error)

    def led_off(self):
        if self.sensor is not None:
            self.sensor.led_off()

    def led_on(self):
        if self.sensor is not None:
            self.sensor.led_on()

    def get_latest(self):
        return self.latest


# Backwards-compatible alias if old code imports RGBLogger.
RGBLogger = RGBSensorControl
