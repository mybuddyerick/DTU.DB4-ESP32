# from config.pins import PINS
# from control.drivers import relay
# import time

# def startup():
#     print ('startup works')

#     laser_relay = relay.Relay("laser module", PINS['laser']['relay'])

#     print(laser_relay)

#     while True:
#         print(1)
#         time.sleep(3)
#         print(2)
#         laser_relay.on()
#         time.sleep(3)
#         laser_relay.off()


from config.pins import PINS
#from control.drivers import relay
from control.drivers.pump import Pump
from control.helpers.peltier import PeltierControl
import time

def startup():
    print ('startup works')

    #laser_relay = relay.Relay("laser module", PINS['laser']['relay'])
    waste_pump = Pump("waste pump", PINS["waste_pump"]["1"], PINS["waste_pump"]["2"])
    peltier = PeltierControl(PINS["peltier"]["relay"])

    

    #print(laser_relay)

    peltier.off()
    waste_pump.on()
    time.sleep(15)
    waste_pump.off()
