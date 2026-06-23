from config.pins import PINS
from config.timings import TIMINGS

from control.helpers.oled_display import OLED
from control.helpers.scheduler import Scheduler
from control.helpers.system_state import SYSTEM_STATE
from control.services.feeding import Feeding

from control.services.websocket_server import WebSocketServer
from control.services.thermal_pid import Thermal_PID

import time
try:
    import ujson as json
except ImportError:
    import json


oled = None
scheduler = None

thermal_pid = None
feeding = None


def startup():
    global oled, scheduler
    global thermal_pid, feeding

    print("starting...")

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])

    thermal_pid = Thermal_PID()
    feeding = Feeding()

    oled.set_status("Found Devices")

    scheduler = Scheduler(step_interval_ms=TIMINGS["step"])

    scheduler.every(
        name="thermal loop",
        interval_ms=TIMINGS["thermal pid upd"],
        runnable=thermal_pid.update
    )

    scheduler.every(
        name="waste loop",
        interval_ms=TIMINGS["feed upd"],
        runnable=feeding.update
    )

    scheduler.every(
        name="oled upd",
        interval_ms=TIMINGS["oled debug"],
        runnable=update_oled,
        run_immediately=True
    )

    ws_server = WebSocketServer(port=81)
    ws_server.start()

    scheduler.every(
        name="ws upd",
        interval_ms=TIMINGS["ws upd"],
        runnable=ws_server.update
    )

    scheduler.every(
        name="ws broadcast",
        interval_ms=TIMINGS["ws broadcast"],
        runnable=lambda: ws_server.broadcast(get_status())
    )
    #scheduler.disable_task(name="thermal loop")
    scheduler.disable_task(name="waste loop")
    scheduler.disable_task(name="ws upd")
    scheduler.disable_task(name="ws broadcast")
    scheduler.disable_task(name="usb broadcast")

    scheduler.every(
        name="usb broadcast",
        interval_ms=1000,
        runnable=lambda: print("USB_DATA:" + json.dumps(get_status()))
    )

    while True:
        step()
        step_wait()


def step():
    # TODO: Receive inputs (POST to update timings/targets etc)
    scheduler.step()


def step_wait():
    scheduler.wait()


def _on_off(value):
    return "ON" if value else "OFF"


def _rgb_sensor_on():
    if feeding is None or feeding.light_sensor is None:
        return False


    try:
        return feeding.light_sensor.found()
    except Exception as exc:
        print("[oled] rgb status error:", exc)
        return False


def update_oled():
    if oled is None:
        return

    temp_c = None
    cooler_running = False
    waste_running = False

    if thermal_pid is not None:
        temp_c = thermal_pid.current_temp_c
        cooler_running = thermal_pid.cooler_pump.running

    if feeding is not None:
        waste_running = feeding.waste_pump.running

    if temp_c is None:
        temp_line = "Temp: --.- C"
    else:
        temp_line = "Temp: {:.1f} C".format(temp_c)

    pump_line = "C:{} W:{}".format(
        _on_off(cooler_running),
        _on_off(waste_running)
    )

    rgb_line = "RGB: {}".format(_on_off(_rgb_sensor_on()))

    oled.update_message(
        "DB4 Status",
        temp_line,
        pump_line,
        rgb_line
    )

def get_status():
    #rgb_values = _safe_get_latest(rgb_sensor)
    #temp_values = _safe_get_latest(temperature)
    #cooler_state = _cooler_running(pumps)
    #waste_state = _waste_running(pumps)
    #peltier_state = peltier.running()
    SYSTEM_STATE["uptime_ms"] = time.ticks_ms()
    return SYSTEM_STATE
