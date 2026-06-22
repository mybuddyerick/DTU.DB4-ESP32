from machine import Pin
from time import ticks_ms, ticks_diff


class StopButton:
    def __init__(self, pin=0, active_low=True, debounce_ms=50):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.active_low = active_low
        self.debounce_ms = debounce_ms
        self.pressed_since = None

    def pressed(self):
        value = self.pin.value()

        if self.active_low:
            is_pressed = value == 0
        else:
            is_pressed = value == 1

        if not is_pressed:
            self.pressed_since = None
            return False

        now = ticks_ms()

        if self.pressed_since is None:
            self.pressed_since = now
            return False

        return ticks_diff(now, self.pressed_since) >= self.debounce_ms