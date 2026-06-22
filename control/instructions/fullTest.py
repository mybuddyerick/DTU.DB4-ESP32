from config.pins import PINS
from config.timings import TIMINGS

from control.helpers.oled_display import OLED
from control.drivers.relay import Relay
from control.helpers.peltier import PeltierControl
from control.helpers.scheduler import Scheduler


count = 0

oled = None
peltier = None
laser_relay = None
scheduler = None


def startup():
    global oled, peltier, laser_relay, scheduler

    print("starting...")

    oled = OLED(PINS["oled"]["sda"], PINS["oled"]["scl"], PINS["oled"]["addr"])
    peltier = PeltierControl(PINS["peltier"]["relay"])
    laser_relay = Relay("laser module", PINS["laser"]["relay"])

    oled.set_status("Found Devices")
    peltier.off()

    scheduler = Scheduler(step_interval_ms=TIMINGS["step"])

    scheduler.every(
        name="oled counter",
        interval_ms=TIMINGS["oled debug"],
        runnable=update_oled_counter,
        run_immediately=True
    )

    scheduler.every(
        name="thermal loop",
        interval_ms=TIMINGS["thermal pid upd"],
        runnable=update_thermal_loop
    )

    scheduler.every(
        name="waste loop",
        interval_ms=TIMINGS["feed upd"],
        runnable=update_waste_loop
    )

    while True:
        step()
        step_wait()


def step():
    # TODO: Receive inputs (POST to update timings/targets etc)
    scheduler.step()


def step_wait():
    scheduler.wait()


def update_oled_counter():
    global count

    oled.update_message(nline1=str(count))
    count += 1


def update_thermal_loop():
    pass


def update_waste_loop():
    pass