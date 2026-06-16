from machine import Pin
from time import ticks_ms, ticks_diff


class Pump:
    def __init__(self, name, pin_a, pin_b):
        self.name = name
        self.pin_a = Pin(pin_a, Pin.OUT)
        self.pin_b = Pin(pin_b, Pin.OUT)

        self.running = False
        self.started_at = 0
        self.duration_ms = 0

        self.off()

    def on(self):
        self.pin_a.value(1)
        self.pin_b.value(0)
        self.running = True
        self.duration_ms = 0
        print(self.name, "ON")

    def reverse(self):
        self.pin_a.value(0)
        self.pin_b.value(1)
        self.running = True
        self.duration_ms = 0
        print(self.name, "REVERSE")

    def off(self):
        self.pin_a.value(0)
        self.pin_b.value(0)
        self.running = False
        self.duration_ms = 0
        print(self.name, "OFF")

    def run_for(self, duration_ms):
        self.pin_a.value(1)
        self.pin_b.value(0)

        self.running = True
        self.started_at = ticks_ms()
        self.duration_ms = duration_ms

        print(self.name, "ON for", duration_ms, "ms")

    def update(self):
        if self.running and self.duration_ms > 0:
            elapsed = ticks_diff(ticks_ms(), self.started_at)

            if elapsed >= self.duration_ms:
                self.off()