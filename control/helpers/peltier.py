from control.drivers.relay import Relay


class PeltierControl:
    def __init__(self, relay_pin=32):
        self.relay = Relay(
            name="Peltier relay",
            pin=relay_pin,
            active_low=True
        )

        print("Peltier relay initialized.")

    def on(self):
        self.relay.on()
        print("Peltier relay on.")

    def off(self):
        self.relay.off()
        print("Peltier relay off.")

    def run_for(self, duration_ms):
        self.relay.run_for(duration_ms)
        print("Peltier relay run for.")

    def update(self):
        self.relay.update()
        print("Peltier relay update.")

    def running(self):
        return self.relay.running
