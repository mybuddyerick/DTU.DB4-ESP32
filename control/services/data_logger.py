import os
import time


class DataLogger:
    DATA_DIR = "/data"
    FILE_PREFIX = "data"
    FILE_EXT = ".csv"

    def __init__(self, thermal_pid=None, feeding=None):
        self.thermal_pid = thermal_pid
        self.feeding = feeding

        self.file_path = self._create_new_file()
        print("[data_logger] logging to", self.file_path)

    def _ensure_data_dir(self):
        try:
            os.listdir(self.DATA_DIR)
        except OSError:
            os.mkdir(self.DATA_DIR)
            print("[data_logger] created directory", self.DATA_DIR)

    def _next_file_path(self):
        index = 1

        while True:
            file_path = "{}/{}{}{}".format(
                self.DATA_DIR,
                self.FILE_PREFIX,
                index,
                self.FILE_EXT
            )

            try:
                with open(file_path, "r"):
                    pass

                index += 1

            except OSError:
                return file_path

    def _create_new_file(self):
        self._ensure_data_dir()

        file_path = self._next_file_path()

        with open(file_path, "w") as file:
            file.write(
                "uptime_ms,"
                "temperature_c,"
                "target_temp_c,"
                "error_c,"
                "output_percent,"
                "cooling,"
                "cooling_phase,"
                "peltier,"
                "cooler_pump,"
                "waste_pump,"
                "rgb_sensor,"
                "od_green_raw,"
                "od_density\n"
            )

        return file_path

    def _on_off(self, value):
        return "ON" if value else "OFF"

    def _csv_value(self, value):
        if value is None:
            return ""

        if isinstance(value, float):
            return "{:.2f}".format(value)

        return str(value)

    def _rgb_sensor_on(self):
        if self.feeding is None or self.feeding.light_sensor is None:
            return False

        try:
            return self.feeding.light_sensor.found()
        except Exception as exc:
            print("[data_logger] rgb status error:", exc)
            return False

    def _od_green(self):
        if self.feeding is None or not hasattr(self.feeding, "last_green"):
            return None
        return self.feeding.last_green

    def _od_density(self):
        if self.feeding is None or not hasattr(self.feeding, "current_density"):
            return None
        return self.feeding.current_density

    def _cooler_pump_on(self):
        if self.thermal_pid is None:
            return False

        try:
            return self.thermal_pid.cooler_pump.running
        except Exception:
            return False

    def _waste_pump_on(self):
        if self.feeding is None:
            return False

        try:
            return self.feeding.waste_pump.running
        except Exception:
            return False

    def _peltier_on(self):
        if self.thermal_pid is None:
            return False

        try:
            return self.thermal_pid.cooling
        except Exception:
            return False

    def write(self):
        try:
            uptime_ms = time.ticks_ms()

            temperature_c = None
            target_temp_c = None
            error_c = None
            output_percent = None
            cooling = False
            cooling_phase = "off"

            if self.thermal_pid is not None:
                temperature_c = self.thermal_pid.current_temp_c
                target_temp_c = self.thermal_pid.target_temp_c
                output_percent = self.thermal_pid.output_percent
                cooling = self.thermal_pid.cooling

                if temperature_c is not None and target_temp_c is not None:
                    error_c = temperature_c - target_temp_c

                if hasattr(self.thermal_pid, "cooling_phase"):
                    cooling_phase = self.thermal_pid.cooling_phase

            row = [
                uptime_ms,
                temperature_c,
                target_temp_c,
                error_c,
                output_percent,
                self._on_off(cooling),
                cooling_phase,
                self._on_off(self._peltier_on()),
                self._on_off(self._cooler_pump_on()),
                self._on_off(self._waste_pump_on()),
                self._on_off(self._rgb_sensor_on()),
                self._od_green(),
                self._od_density(),
            ]

            with open(self.file_path, "a") as file:
                file.write(",".join(self._csv_value(value) for value in row) + "\n")

            print("[data_logger] wrote row to", self.file_path)

        except Exception as exc:
            print("[data_logger] write error:", exc)