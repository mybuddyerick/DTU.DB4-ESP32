from machine import Pin, SoftI2C

from control.drivers.oled_driver import SSD1306_I2C


class OLEDDisplay:
    def __init__(self, sda_pin=4, scl_pin=2, addr=0x3C):
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin
        self.addr = addr

        self.display = None
        self.enabled = False

        try:
            i2c = SoftI2C(
                sda=Pin(sda_pin),
                scl=Pin(scl_pin),
                freq=100000
            )

            print("Scanning OLED I2C bus on SDA GPIO", sda_pin, "and SCL GPIO", scl_pin)
            devices = i2c.scan()
            print("OLED devices:", [hex(device) for device in devices])

            if addr not in devices:
                print("OLED not found. OLED disabled.")
                return

            self.display = SSD1306_I2C(
                128,
                64,
                i2c,
                addr=addr
            )

            self.enabled = True

            self.display.fill(0)
            self.display.text("DB4 ESP32", 0, 0)
            self.display.text("OLED ready", 0, 16)
            self.display.show()

            print("OLED initialized.")

        except Exception as error:
            print("OLED setup failed:", error)

    def update(self, rgb_values=None, temp_values=None, pumps=None, peltier=None):
        if not self.enabled:
            return

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
