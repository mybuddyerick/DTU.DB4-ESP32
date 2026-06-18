from config.pins import PINS
from config.timings import TIMINGS
from control.helpers.oled_display import OLED
from control.drivers.relay import Relay
from control.helpers.peltier import PeltierControl
from control.helpers.web_sockets import WebSocketServer # 1. Import the WebSocket

import time

count = 0

oled: OLED = None
peltier: PeltierControl = None
laser_relay: Relay = None
ws_server: WebSocketServer = None # 2. Add server variable

def startup():
    global oled, peltier, laser_relay, ws_server
    print ('starting...')

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])
    peltier = PeltierControl(PINS["peltier"]["relay"])
    laser_relay = Relay("laser module", PINS['laser']['relay'])

    # 3. Start the WebSocket Server
    ws_server = WebSocketServer(port=81)
    ws_server.start()

    oled.set_status("Found Devices")

    peltier.off()

    # Begin Mainloop
    while True: # Until breaking condition is implemented
        ws_server.update() # 4. Keep the server listening for the Mac
        step()
        step_wait()

def step():
    global oled, count, ws_server

    oled.update_message(nline1=str(count))
    
    # 5. Broadcast a "Fake" JSON status to the React Dashboard
    dummy_status = {
        "available": True,
        "uptime_ms": count * 500, # Fake uptime
        "system": { "free_memory": 100000 },
        "rgb": {
            "available": True,
            "sensor_enabled": True,
            "logging": True,
            "time_ms": count * 500,
            "clear": 1000,
            "red": count,   # Watch the red value count up!
            "green": 255,
            "blue": 100
        },
        "temperature": {
            "available": True,
            "sensor_enabled": True,
            "logging": True,
            "time_ms": count * 500,
            "temp_c": 25.5 + (count * 0.1), # Watch temperature rise!
            "raw_average": 2000,
            "voltage": 1.5,
            "resistance": 10000
        },
        "outputs": {
            "water_pump": count % 2 == 0, # Toggles every tick
            "spray_pump": False,
            "peltier": False
        }
    }
    
    ws_server.broadcast(dummy_status)
    count += 1

def step_wait():
    time.sleep(TIMINGS["step"])