from machine import Pin, I2C
from time import sleep

TCS34725_ADDR = 0x29

COMMAND_BIT = 0x80
AUTO_INCREMENT = 0x20

ENABLE = 0x00
ATIME = 0x01
CONTROL = 0x0F
ID = 0x12
STATUS = 0x13

CDATA = 0x14
RDATA = 0x16
GDATA = 0x18
BDATA = 0x1A


class TCS34725:
    def __init__(self, sda_pin=21, scl_pin=22, freq=50000, led_pin=None, led_active_high=True):
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin
        self.led_active_high = led_active_high

        self.i2c = I2C(
            0,
            sda=Pin(sda_pin),
            scl=Pin(scl_pin),
            freq=freq
        )

        self.led = None

        if led_pin is not None:
            self.led = Pin(led_pin, Pin.OUT)
            self.led_off()

    def led_on(self):
        if self.led is not None:
            self.led.value(1 if self.led_active_high else 0)

    def led_off(self):
        if self.led is not None:
            self.led.value(0 if self.led_active_high else 1)

    def scan(self):
        try:
            return self.i2c.scan()
        except OSError:
            return []

    def found(self):
        return TCS34725_ADDR in self.scan()

    def write_reg(self, reg, value):
        self.i2c.writeto_mem(
            TCS34725_ADDR,
            COMMAND_BIT | reg,
            bytes([value])
        )

    def read_reg(self, reg):
        data = self.i2c.readfrom_mem(
            TCS34725_ADDR,
            COMMAND_BIT | reg,
            1
        )
        return data[0]

    def read_word(self, reg):
        data = self.i2c.readfrom_mem(
            TCS34725_ADDR,
            COMMAND_BIT | AUTO_INCREMENT | reg,
            2
        )
        return data[0] | (data[1] << 8)

    def sensor_id(self):
        return self.read_reg(ID)

    def init(self):
        self.led_off()

        # Power on
        self.write_reg(ENABLE, 0x01)
        sleep(0.1)

        # Enable RGBC ADC
        self.write_reg(ENABLE, 0x03)
        sleep(0.1)

        # Integration time: around 50 ms
        self.write_reg(ATIME, 0xEB)
        sleep(0.05)

        # Gain:
        # 0x00 = 1x
        # 0x01 = 4x
        # 0x02 = 16x
        # 0x03 = 60x
        self.write_reg(CONTROL, 0x01)
        sleep(0.2)

    def data_ready(self):
        return (self.read_reg(STATUS) & 0x01) == 0x01

    def read_raw(self):
        if not self.data_ready():
            return None

        return {
            "clear": self.read_word(CDATA),
            "red": self.read_word(RDATA),
            "green": self.read_word(GDATA),
            "blue": self.read_word(BDATA)
        }

    def read_color(self):
        return self.read_raw()
