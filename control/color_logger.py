import os
from time import ticks_ms, ticks_diff

from control.tcs34725 import TCS34725


class ColorLogger:
    def __init__(self, csv_path="/data/color.csv", interval_ms=5000, sda_pin=2, scl_pin=4):
        self.csv_path = csv_path
        self.interval_ms = interval_ms
        self.last_log = ticks_ms()
        self.enabled = False
        self.sensor = None

        self._ensure_data_folder()

        try:
            self.sensor = TCS34725(
                sda_pin=sda_pin,
                scl_pin=scl_pin
            )

            if not self.sensor.found():
                print("TCS34725 not found. Color logging disabled.")
                return

            print("TCS34725 found. Sensor ID:", hex(self.sensor.sensor_id()))

            self.sensor.init()
            self._ensure_csv_header()

            self.enabled = True
            print("Color logging enabled:", self.csv_path)

        except Exception as e:
            print("Color logger setup failed:", e)
            self.enabled = False

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
                file.write("time,red,green,blue,clear\n")

    def update(self):
        if not self.enabled:
            return

        now = ticks_ms()

        if ticks_diff(now, self.last_log) < self.interval_ms:
            return

        self.last_log = now

        try:
            color = self.sensor.read_color()

            if color is None:
                return

            time_s = now // 1000

            line = "{},{},{},{},{}\n".format(
                time_s,
                color["red"],
                color["green"],
                color["blue"],
                color["clear"]
            )

            with open(self.csv_path, "a") as file:
                file.write(line)

            print("Logged color:", line.strip())

        except Exception as e:
            print("Color logging error:", e)