from config.pins import PINS
from config.timings import TIMINGS
from control.helpers.oled_display import OLED
from control.drivers.relay import Relay
from control.helpers.peltier import PeltierControl

import time

count = 0

oled: OLED = None
peltier: PeltierControl = None
laser_relay: Relay = None

def startup():
    global oled, peltier, laser_relay
    print ('starting...')

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])
    peltier = PeltierControl(PINS["peltier"]["relay"])
    laser_relay = Relay("laser module", PINS['laser']['relay'])

    oled.set_status("Found Devices")

    peltier.off()

    # Begin Mainloop
    while True: # Until breaking condition is implemented
        step()
        step_wait()

def step():
    global oled, count

    oled.update_message(nline1=str(count))
    count += 1

def step_wait():
    time.sleep(TIMINGS["step"])