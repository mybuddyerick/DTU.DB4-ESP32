from config.pins import PINS
from config.timings import TIMINGS

from control.helpers.oled_display import OLED
from control.helpers.scheduler import Scheduler
from control.helpers.system_state import SYSTEM_STATE
from control.services.feeding import Feeding
from control.services.websocket_server import WebSocketServer
from control.services.thermal_pid import Thermal_PID
from control.services.data_logger import DataLogger

import time

try:
    import ujson as json
except ImportError:
    import json


oled = None
scheduler = None

thermal_pid = None
feeding = None
data_logger = None


def startup():
    global oled, scheduler
    global thermal_pid, feeding, data_logger

    print("starting...")

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])

    thermal_pid = Thermal_PID()
    feeding = Feeding()

    data_logger = DataLogger(
        thermal_pid=thermal_pid,
        feeding=feeding
    )

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

    scheduler.every(
        name="csv log",
        interval_ms=10000,
        runnable=data_logger.write,
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

    scheduler.every(
        name="usb broadcast",
        interval_ms=1000,
        runnable=lambda: print("USB_DATA:" + json.dumps(get_status()))
    )

    #scheduler.disable_task(name="waste loop")
    #scheduler.disable_task(name="usb broadcast")
    #scheduler.disable_task(name="thermal loop")
    scheduler.disable_task(name="ws upd")
    scheduler.disable_task(name="ws broadcast")
    #scheduler.disable_task(name="csv log")

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


def _peltier_on():
    if thermal_pid is None:
        return False

    try:
        # In your thermal_pid cycle, peltier is ON whenever cooling is active.
        return thermal_pid.cooling

    except Exception as exc:
        print("[oled] peltier status error:", exc)
        return False


def update_oled():
    try:
        if oled is None:
            return

        temp_c = None
        cooler_running = False
        waste_running = False

        if thermal_pid is not None:
            temp_c = thermal_pid.current_temp_c

            if hasattr(thermal_pid.cooler_pump, "running"):
                cooler_running = thermal_pid.cooler_pump.running

        if feeding is not None:
            if hasattr(feeding.waste_pump, "running"):
                waste_running = feeding.waste_pump.running

        if temp_c is None:
            temp_line = "Temp: --.- C"
        else:
            temp_line = "Temp: {:.1f} C".format(temp_c)

        pump_line = "C:{} W:{}".format(
            _on_off(cooler_running),
            _on_off(waste_running)
        )

        peltier_line = "Peltier: {}".format(_on_off(_peltier_on()))

        oled.update_message(
            "DB4 Status",
            temp_line,
            pump_line,
            peltier_line
        )

    except Exception as exc:
        print("[oled] update error:", exc)


def get_status():
    SYSTEM_STATE["uptime_ms"] = time.ticks_ms()

    if thermal_pid is not None:
        if thermal_pid.current_temp_c is not None:
            SYSTEM_STATE["temperature"]["temp_c"] = thermal_pid.current_temp_c
        SYSTEM_STATE["outputs"]["water_pump"] = getattr(thermal_pid.cooler_pump, "running", False)
        SYSTEM_STATE["outputs"]["peltier"] = thermal_pid.cooling

    if feeding is not None:
        SYSTEM_STATE["outputs"]["spray_pump"] = getattr(feeding.waste_pump, "running", False)
        if hasattr(feeding, "last_green"):
            SYSTEM_STATE["rgb"]["green"] = feeding.last_green
        if hasattr(feeding, "current_density") and feeding.current_density is not None:
            SYSTEM_STATE["rgb"]["od"] = feeding.current_density

    return SYSTEM_STATE