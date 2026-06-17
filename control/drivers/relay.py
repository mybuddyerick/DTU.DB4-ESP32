from machine import Pin
from time import ticks_ms, ticks_diff


class Relay:
    def __init__(self, name, pin, active_low=True):
        self.name = name
        self.pin = Pin(pin, Pin.OUT)
        self.active_low = active_low

        self.running = False
        self.started_at = 0
        self.duration_ms = 0

        self.off()

    def on(self):
        if self.active_low:
            self.pin.value(0)
        else:
            self.pin.value(1)

        self.running = True
        self.duration_ms = 0
        print(self.name, "ON")

    def off(self):
        if self.active_low:
            self.pin.value(1)
        else:
            self.pin.value(0)

        self.running = False
        self.duration_ms = 0
        print(self.name, "OFF")

    def run_for(self, duration_ms):
        self.on()
        self.started_at = ticks_ms()
        self.duration_ms = duration_ms
        print(self.name, "ON for", duration_ms, "ms")

    def update(self):
        if self.running and self.duration_ms > 0:
            elapsed = ticks_diff(ticks_ms(), self.started_at)
            if elapsed >= self.duration_ms:
                self.off()
