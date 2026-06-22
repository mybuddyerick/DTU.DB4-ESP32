from config.pins import PINS
from config.timings import TIMINGS

from control.helpers.oled_display import OLED
from control.drivers.relay import Relay
from control.helpers.scheduler import Scheduler
from control.services.websocket_server import WebSocketServer


oled = None
peltier = None
laser_relay = None
scheduler = None


def startup():
    global oled, peltier, laser_relay, scheduler

    print("starting...")

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])
    peltier = Relay("peltier", PINS["peltier"]["relay"])
    laser_relay = Relay("laser module", PINS["laser"]["relay"])

    oled.set_status("Found Devices")
    peltier.off()

    scheduler = Scheduler(step_interval_ms=TIMINGS["step"])
    '''
    scheduler.every(
        name="thermal loop",
        interval_ms=TIMINGS["thermal pid upd"],
        runnable=pass
    )

    scheduler.every(
        name="waste loop",
        interval_ms=TIMINGS["feed upd"],
        runnable=update_waste_loop
    )
    '''
    ws_server = WebSocketServer(port=81)
    ws_server.start()

    scheduler.every(
        name="ws upd",
        interval_ms=TIMINGS["ws upd"],
        runnable=ws_server.update()
    )

    scheduler.every(
        name="ws broadcast",
        interval_ms=TIMINGS["ws broadcast"],
        runnable=ws_server.broadcast(get_status())
    )

    while True:
        step()
        step_wait()


def step():
    # TODO: Receive inputs (POST to update timings/targets etc)
    scheduler.step()


def step_wait():
    scheduler.wait()


def get_status():
    #rgb_values = _safe_get_latest(rgb_sensor)
    #temp_values = _safe_get_latest(temperature)

    #cooler_state = _cooler_running(pumps)
    #waste_state = _waste_running(pumps)
    #peltier_state = peltier.running()

    dummy_status = {
        "available": True,
        "uptime_ms": 1,
        "system": {"free_memory": 100000},
        "rgb": {
            "available": True,
            "sensor_enabled": True,
            "logging": True,
            "time_ms": 1,
            "clear": 1000,
            "red": 1,
            "green": 255,
            "blue": 100
        },
        "temperature": {
            "available": True,
            "sensor_enabled": True,
            "logging": True,
            "time_ms": 1,
            "temp_c": 25.5,
            "raw_average": 2000,
            "voltage": 1.5,
            "resistance": 10000
        },
        "outputs": {
            "water_pump": False,
            "spray_pump": False,
            "peltier": False
        }
    }

    return dummy_status