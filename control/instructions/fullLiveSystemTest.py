from time import sleep_ms, ticks_ms, ticks_diff
import sys

from machine import Pin

from config.pins import PINS
from config.directories import PATHS
from config.timings import TIMINGS

from control.drivers import relay
from control.temperature import TemperatureControl
from control.rgb_sensor import RGBSensorControl
from control.helpers.pumps import PumpsControl
from control.helpers.peltier import PeltierControl
from control.helpers.oled_display import OLED

if "/site" not in sys.path:
    sys.path.append("/site")

from live_dashboard import LiveDashboard
from control.helpers.web_sockets import WebSocketServer

OLED_UPDATE_MS = 1000
TERMINAL_UPDATE_MS = 1000

STOP_BUTTON_PIN = 0

WASTE_PUMP_ON_MS = 5000
WASTE_PUMP_OFF_MS = 15000


def _oled_addr():
    addr = PINS["oled"]["addr"]

    if isinstance(addr, str):
        return int(addr, 16)

    return addr


def _on_off(value):
    if value:
        return "ON"
    return "OFF"


def _safe_get_latest(obj):
    try:
        if obj is None:
            return None

        return obj.get_latest()

    except Exception:
        return None


def _cooler_running(pumps):
    # Cooler pump = 5V pump = old "water" pump in PumpsControl
    return pumps.water_running()


def _waste_running(pumps):
    # Waste pump = 12V pump = old "spray" pump in PumpsControl
    return pumps.spray_running()


def _cooler_on(pumps):
    pumps.water_on()


def _waste_on(pumps):
    pumps.spray_on()


def _cooler_off(pumps):
    pumps.water_off()


def _waste_off(pumps):
    pumps.spray_off()


def _button_pressed(button):
    # GPIO0 / BOOT button is normally active-low.
    return button.value() == 0


def _shutdown_all(oled, pumps, peltier, laser_relay, dashboard):
    print()
    print("Stopping full live system test.")
    print("Turning all outputs OFF.")

    if pumps is not None:
        try:
            _cooler_off(pumps)
            _waste_off(pumps)
        except Exception as error:
            print("Pump shutdown error:", error)

    if peltier is not None:
        try:
            peltier.off()
        except Exception as error:
            print("Peltier shutdown error:", error)

    if laser_relay is not None:
        try:
            laser_relay.off()
        except Exception as error:
            print("Laser relay shutdown error:", error)

    if oled is not None:
        try:
            oled.update_message(
                "Full Live Test",
                "STOPPED",
                "Outputs OFF"
            )
        except Exception:
            pass

    if dashboard is not None:
        try:
            dashboard.stop()
        except Exception as error:
            print("Dashboard stop error:", error)


def _update_oled(oled, rgb_values, temp_values, pumps, peltier, laser_on):
    if oled is None:
        return

    try:
        temp_text = "Temp: -- C"

        if temp_values is not None:
            temp_text = "Temp: {:.1f} C".format(temp_values["temp_c"])

        green_text = "Green: --"

        if rgb_values is not None:
            green_text = "Green: {}".format(rgb_values["green"])

        pump_text = "Cool:{} Waste:{}".format(
            _on_off(_cooler_running(pumps)),
            _on_off(_waste_running(pumps))
        )

        output_text = "Pel:{} Las:{}".format(
            _on_off(peltier.running()),
            _on_off(laser_on)
        )

        oled.update_message(
            "Full Live Test",
            temp_text,
            green_text,
            pump_text + " " + output_text
        )

    except Exception as error:
        print("OLED update error:", error)


def _print_status(rgb_values, temp_values, pumps, peltier, laser_on, waste_cycle_state):
    print()
    print("===== FULL LIVE SYSTEM TEST =====")

    if temp_values is None:
        print("Temperature: no data yet")
    else:
        print("Temperature:", "{:.2f} C".format(temp_values["temp_c"]))

    if rgb_values is None:
        print("Green light: no data yet")
    else:
        print("Green light:", rgb_values["green"])

    print("Cooler pump 5V:", _on_off(_cooler_running(pumps)))
    print("Waste pump 12V:", _on_off(_waste_running(pumps)))
    print("Waste pump cycle:", waste_cycle_state)
    print("Peltier:", _on_off(peltier.running()))
    print("Laser relay:", _on_off(laser_on))
    print("Stop button: GPIO 0")
    print("Dashboard: http://192.168.4.1")


def startup():
    oled = None
    pumps = None
    peltier = None
    laser_relay = None
    dashboard = None

    laser_state = {
        "on": False
    }

    waste_cycle = {
        "state": "ON",
        "last_change": ticks_ms()
    }

    print()
    print("====================================")
    print(" FULL LIVE SYSTEM TEST")
    print("====================================")
    print("Cooler pump 5V: always ON")
    print("Waste pump 12V: 5 seconds ON, 15 seconds OFF")
    print("OLED: ON, only green RGB value shown")
    print("Web dashboard: ON")
    print("RGB sensor: ON")
    print("Temperature sensor: ON")
    print("Peltier: OFF")
    print("Laser relay: ON")
    print("Stop button: GPIO 0")
    print()

    try:
        stop_button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

        oled = OLED(
            sda_pin=PINS["oled"]["sda"],
            scl_pin=PINS["oled"]["scl"],
            addr=_oled_addr()
        )

        oled.update_message(
            "Full Live Test",
            "Starting...",
            "GPIO0 stops"
        )

        temperature = TemperatureControl(
            csv_path=PATHS["temperature_csv"],
            interval_ms=int(TIMINGS["temperature_log_interval"] * 1000),
            adc_pin=PINS["temperature"]["adc"],
            verbose=True
        )

        rgb_sensor = RGBSensorControl(
            csv_path=PATHS["rgb_csv"],
            interval_ms=int(TIMINGS["rgb_log_interval"] * 1000),
            sda_pin=PINS["rgb"]["sda"],
            scl_pin=PINS["rgb"]["scl"],
            led_pin=PINS["rgb"]["led"],
            verbose=True
        )

        pumps = PumpsControl(
            water_pin_a=PINS["water_pump"]["1"],
            water_pin_b=PINS["water_pump"]["2"],
            spray_pin_a=PINS["waste_pump"]["1"],
            spray_pin_b=PINS["waste_pump"]["2"]
        )

        peltier = PeltierControl(
            relay_pin=PINS["peltier"]["relay"]
        )

        laser_relay = relay.Relay(
            "laser module",
            PINS["laser"]["relay"]
        )

        print(laser_relay)

        # Initial required output states
        _cooler_on(pumps)
        _waste_on(pumps)

        peltier.off()

        laser_relay.on()
        laser_state["on"] = True

        start_time = ticks_ms()

        def status_func():
            rgb_values = _safe_get_latest(rgb_sensor)
            temp_values = _safe_get_latest(temperature)

            cooler_state = _cooler_running(pumps)
            waste_state = _waste_running(pumps)
            peltier_state = peltier.running()

            return {
                "available": True,
                "uptime_ms": ticks_diff(ticks_ms(), start_time),

                "system": {
                    "mode": "full live system test",
                    "dashboard": "running",
                    "stop_button_pin": STOP_BUTTON_PIN,
                    "waste_pump_cycle": waste_cycle["state"],
                    "waste_pump_on_ms": WASTE_PUMP_ON_MS,
                    "waste_pump_off_ms": WASTE_PUMP_OFF_MS,
                    "note": "cooler_pump is 5V, waste_pump is 12V"
                },

                "rgb": {
                    "available": rgb_values is not None,
                    "sensor_enabled": rgb_sensor.enabled,
                    "logging": rgb_sensor.log_enabled,
                    "time_ms": None if rgb_values is None else rgb_values["time_ms"],
                    "clear": None if rgb_values is None else rgb_values["clear"],
                    "red": None if rgb_values is None else rgb_values["red"],
                    "green": None if rgb_values is None else rgb_values["green"],
                    "blue": None if rgb_values is None else rgb_values["blue"]
                },

                "temperature": {
                    "available": temp_values is not None,
                    "sensor_enabled": temperature.enabled,
                    "logging": temperature.log_enabled,
                    "time_ms": None if temp_values is None else temp_values["time_ms"],
                    "temp_c": None if temp_values is None else temp_values["temp_c"],
                    "raw_average": None if temp_values is None else temp_values["raw_average"],
                    "voltage": None if temp_values is None else temp_values["voltage"],
                    "resistance": None if temp_values is None else temp_values["resistance"]
                },

                "outputs": {
                    # New names
                    "cooler_pump": cooler_state,
                    "waste_pump": waste_state,
                    "peltier": peltier_state,
                    "laser_relay": laser_state["on"],

                    # Backwards-compatible names for current dashboard JS
                    "water_pump": cooler_state,
                    "spray_pump": waste_state
                }
            }

        dashboard = LiveDashboard(
            rgb_sensor=rgb_sensor,
            temperature=temperature,
            pumps=pumps,
            peltier=peltier,
            status_func=status_func
        )

        dashboard.start()

        ws_server = WebSocketServer(port=81)
        ws_server.start()

        last_oled_update = ticks_ms()
        last_terminal_update = ticks_ms()
        last_ws_update = ticks_ms()

        oled.update_message(
            "Full Live Test",
            "System running",
            "GPIO0 stops",
            "192.168.4.1"
        )

        while True:
            now = ticks_ms()

            # Stop immediately when GPIO0 button is pressed
            if _button_pressed(stop_button):
                sleep_ms(50)

                if _button_pressed(stop_button):
                    print("Stop button pressed.")
                    _shutdown_all(oled, pumps, peltier, laser_relay, dashboard)
                    return

            dashboard.update()
            ws_server.update()

            rgb_values = rgb_sensor.update()
            temp_values = temperature.update()

            # Cooler pump stays ON all the time
            if not _cooler_running(pumps):
                print("Cooler pump 5V was OFF. Turning back ON.")
                _cooler_on(pumps)

            # Waste pump runs 5 seconds ON, then 15 seconds OFF
            if waste_cycle["state"] == "ON":
                if not _waste_running(pumps):
                    _waste_on(pumps)

                if ticks_diff(now, waste_cycle["last_change"]) >= WASTE_PUMP_ON_MS:
                    print("Waste pump 12V cycle: OFF for 15 seconds.")
                    _waste_off(pumps)
                    waste_cycle["state"] = "OFF"
                    waste_cycle["last_change"] = now

            else:
                if _waste_running(pumps):
                    _waste_off(pumps)

                if ticks_diff(now, waste_cycle["last_change"]) >= WASTE_PUMP_OFF_MS:
                    print("Waste pump 12V cycle: ON for 5 seconds.")
                    _waste_on(pumps)
                    waste_cycle["state"] = "ON"
                    waste_cycle["last_change"] = now

            # Keep Peltier OFF all the time
            if peltier.running():
                print("Peltier was ON. Turning back OFF.")
                peltier.off()

            # Keep laser relay ON all the time
            if not laser_state["on"]:
                print("Laser relay was OFF. Turning back ON.")
                laser_relay.on()
                laser_state["on"] = True

            pumps.update()
            peltier.update()

            if ticks_diff(now, last_oled_update) >= OLED_UPDATE_MS:
                last_oled_update = now
                _update_oled(
                    oled,
                    rgb_values,
                    temp_values,
                    pumps,
                    peltier,
                    laser_state["on"]
                )

            if ticks_diff(now, last_terminal_update) >= TERMINAL_UPDATE_MS:
                last_terminal_update = now
                _print_status(
                    rgb_values,
                    temp_values,
                    pumps,
                    peltier,
                    laser_state["on"],
                    waste_cycle["state"]
                )

            if ticks_diff(now, last_ws_update) >= 500:
                last_ws_update = now
                ws_server.broadcast(status_func())

            sleep_ms(int(TIMINGS["step"] * 1000))

    except KeyboardInterrupt:
        print("Full live system test stopped manually.")
        _shutdown_all(oled, pumps, peltier, laser_relay, dashboard)

    except Exception as error:
        print("Full live system test crashed:", error)

        try:
            sys.print_exception(error)
        except Exception:
            pass

        _shutdown_all(oled, pumps, peltier, laser_relay, dashboard)

        raise