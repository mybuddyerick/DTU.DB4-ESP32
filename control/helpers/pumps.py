from control.drivers.pump import Pump


class PumpsControl:
    def __init__(
        self,
        cooler_pin_a=18,
        cooler_pin_b=19,
        waste_pin_a=25,
        waste_pin_b=26
    ):
        self.cooler = Pump(
            name="cooler_pump 5V",
            pin_a=cooler_pin_a,
            pin_b=cooler_pin_b
        )

        self.waste = Pump(
            name="waste_pump 12V",
            pin_a=waste_pin_a,
            pin_b=waste_pin_b
        )

        print("Pumps initialized.")

    def run_cooler_for(self, duration_ms):
        self.cooler.run_for(duration_ms)

    def run_waste_for(self, duration_ms):
        self.waste.run_for(duration_ms)

    def cooler_on(self):
        self.cooler.on()

    def cooler_off(self):
        self.cooler.off()

    def waste_on(self):
        self.waste.on()

    def waste_off(self):
        self.waste.off()

    def cooler_running(self):
        return self.cooler.running

    def waste_running(self):
        return self.waste.running

    def update(self):
        self.cooler.update()
        self.waste.update()
