from machine import Pin, SoftI2C
from time import sleep_ms

from control.drivers.oled import SSD1306_I2C


class OLEDDisplay:
    def __init__(self, sda_pin=4, scl_pin=2, addr=0x3C):
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin
        self.addr = addr

        self.i2c = None
        self.display = None
        self.enabled = False

        self.error_count = 0
        self.max_errors_before_disable = 10

        self._setup()

    def _setup(self):
        try:
            self.i2c = SoftI2C(
                sda=Pin(self.sda_pin),
                scl=Pin(self.scl_pin),
                freq=50000
            )

            print("Scanning OLED I2C bus on SDA GPIO", self.sda_pin, "and SCL GPIO", self.scl_pin)

            devices = self.i2c.scan()
            print("OLED devices:", [hex(device) for device in devices])

            if self.addr not in devices:
                print("OLED not found at", hex(self.addr))
                self.enabled = False
                return

            self.display = SSD1306_I2C(
                128,
                64,
                self.i2c,
                addr=self.addr
            )

            self.enabled = True
            self.error_count = 0

            self.show_message(
                "DB4 ESP32",
                "OLED ready",
                "I2C: {}".format(hex(self.addr))
            )

            print("OLED initialized.")

        except Exception as error:
            print("OLED setup failed:", error)
            self.enabled = False

    def recover(self):
        print("Trying to recover OLED...")

        self.enabled = False
        self.display = None

        sleep_ms(100)

        try:
            devices = self.i2c.scan()
            print("OLED recovery scan:", [hex(device) for device in devices])

            if self.addr not in devices:
                print("OLED still missing.")
                return

            self.display = SSD1306_I2C(
                128,
                64,
                self.i2c,
                addr=self.addr
            )

            self.enabled = True
            self.error_count = 0

            self.show_message(
                "OLED recovered",
                "DB4 running"
            )

            print("OLED recovered.")

        except Exception as error:
            print("OLED recovery failed:", error)

    def _handle_error(self, error):
        self.error_count += 1

        print("OLED error:", error)
        print("OLED error count:", self.error_count)

        if self.error_count >= self.max_errors_before_disable:
            print("OLED disabled after repeated errors.")
            self.enabled = False
            return

        self.recover()

    def show_message(self, line1="", line2="", line3="", line4=""):
        if not self.enabled or self.display is None:
            return

        try:
            self.display.fill(0)

            self.display.text(str(line1), 0, 0)
            self.display.text(str(line2), 0, 16)
            self.display.text(str(line3), 0, 32)
            self.display.text(str(line4), 0, 48)

            self.display.show()

        except OSError as error:
            self._handle_error(error)

    def update(self, rgb_values=None, temp_values=None, pumps=None, peltier=None):
        if not self.enabled or self.display is None:
            return

        try:
            display = self.display
            display.fill(0)

            display.text("DB4 Hardware", 0, 0)

            if temp_values is None:
                display.text("T: --.- C", 0, 10)
            else:
                display.text("T:{:.1f} C".format(temp_values["temp_c"]), 0, 10)

            if rgb_values is None:
                display.text("RGB: no data", 0, 22)
            else:
                display.text(
                    "R:{} G:{}".format(
                        rgb_values["red"],
                        rgb_values["green"]
                    ),
                    0,
                    22
                )

                display.text(
                    "B:{} C:{}".format(
                        rgb_values["blue"],
                        rgb_values["clear"]
                    ),
                    0,
                    34
                )

            if pumps is not None:
                water_status = "ON" if pumps.water_running() else "OFF"
                spray_status = "ON" if pumps.spray_running() else "OFF"
                display.text("P1:{} P2:{}".format(water_status, spray_status), 0, 46)

            if peltier is not None:
                peltier_status = "ON" if peltier.running() else "OFF"
                display.text("TE:{}".format(peltier_status), 0, 56)

            display.show()

        except OSError as error:
            self._handle_error(error)