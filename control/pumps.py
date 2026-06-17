from control.drivers.pump_driver import Pump


class PumpsControl:
    def __init__(
        self,
        water_pin_a=18,
        water_pin_b=19,
        spray_pin_a=25,
        spray_pin_b=26
    ):
        self.water = Pump(
            name="5V water pump",
            pin_a=water_pin_a,
            pin_b=water_pin_b
        )

        self.spray = Pump(
            name="12V spray pump",
            pin_a=spray_pin_a,
            pin_b=spray_pin_b
        )

        print("Pumps initialized.")

    def run_water_for(self, duration_ms):
        self.water.run_for(duration_ms)

    def run_spray_for(self, duration_ms):
        self.spray.run_for(duration_ms)

    def water_on(self):
        self.water.on()

    def water_off(self):
        self.water.off()

    def spray_on(self):
        self.spray.on()

    def spray_off(self):
        self.spray.off()

    def water_running(self):
        return self.water.running

    def spray_running(self):
        return self.spray.running

    def update(self):
        self.water.update()
        self.spray.update()
