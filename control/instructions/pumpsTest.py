from config.pins import PINS
from control.drivers.pump import Pump
from control.helpers.peltier import PeltierControl
import time

def startup():
    print ('startup works')

    waste_pump = Pump("waste pump", PINS["waste_pump"]["1"], PINS["waste_pump"]["2"])
    cooler_pump = Pump("cooler pump", PINS["cooler_pump"]["1"], PINS["cooler_pump"]["2"])
    peltier = PeltierControl(PINS["peltier"]["relay"])

    peltier.off()
    waste_pump.off()

    while True:
        cooler_pump.on()
        time.sleep(10)
        print("pump is still working")
