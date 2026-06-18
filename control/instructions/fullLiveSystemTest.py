from time import sleep_ms, ticks_ms, ticks_diff
import sys

from config.pins import PINS
from config.directories import PATHS
from config.timings import TIMING

from control.drivers import relay
from control.temperature import TemperatureControl
from control.rgb_sensor import RGBSensorControl
from control.helpers.pumps import PumpsControl
from control.helpers.peltier import PeltierControl
from control.oled_display import OLEDDisplay

if "/site" not in sys.path:
    sys.path.append("/site")

from live_dashboard import LiveDashboard


OLED_UPDATE_MS = 1000
TERMINAL_UPDATE_MS = 1000
LASER_REFRESH_MS = 1000


def _oled_addr():
    addr = PINS["oled"]["addr"]

    if isinstance(addr, str):
        return int(addr, 16)

    return addr


def _on_off(value):
    if value:
        return "ON"

    return "OFF"


# The PumpsControl class may still internally call the pumps
# "water" and "spray", but in the experiment naming:
#
# water pump = cooler pump = 5V pump
# spray pump = waste pump = 12V pump

def _cooler_on(pumps):
    pumps.water_on()


def _cooler_off(pumps):
    pumps.water_off()


def _cooler_running(pumps):
    return pumps.water_running()


def _waste_on(pumps):
    pumps.spray_on()


def _waste_off(pumps):
    pumps.spray_off()


def _waste_running(pumps):
    return pumps.spray_running()


def _safe_get_latest(obj):
    try:
        if obj is None:
            return None

        return obj.get_latest()

    except Exception:
        return None


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

        pump_text = "Cooler:{} Waste:{}".format(
            _on_off(_cooler_running(pumps)),
            _on_off(_waste_running(pumps))
        )

        output_text = "Pel:{} Laser:{}".format(
            _on_off(peltier.running()),
            _on_off(laser_on)
        )

        oled.show_message(
            "Full Test",
            temp_text,
            green_text,
            pump_text,
            output_text
        )

    except Exception as error:
        print("OLED update error:", error)


def _print_status(rgb_values, temp_values, pumps, peltier, laser_on):
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
    print("Peltier:", _on_off(peltier.running()))
    print("Laser relay:", _on_off(laser_on))
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

    print()
    print("====================================")
    print(" FULL LIVE SYSTEM TEST")
    print("====================================")
    print("Cooler pump 5V: always ON")
    print("Waste pump 12V: always ON")
    print("OLED: ON")
    print("Web dashboard: ON")
    print("RGB sensor: ON")
    print("Temperature sensor: ON")
    print("Peltier: always OFF")
    print("Laser relay: always ON")
    print()

    try:
        oled = OLEDDisplay(
            sda_pin=PINS["oled"]["sda"],
            scl_pin=PINS["oled"]["scl"],
            addr=_oled_addr()
        )

        oled.show_message(
            "Full Test",
            "Starting...",
            "Please wait"
        )

        temperature = TemperatureControl(
            csv_path=PATHS["temperature_csv"],
            interval_ms=TIMING["temperature_log_interval_ms"],
            adc_pin=PINS["temperature"]["adc"],
            verbose=True
        )

        rgb_sensor = RGBSensorControl(
            csv_path=PATHS["rgb_csv"],
            interval_ms=TIMING["rgb_log_interval_ms"],
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

        # Same style as your working laser relay test.
        laser_relay = relay.Relay(
            "laser module",
            PINS["laser"]["relay"]
        )

        print(laser_relay)

        # Required fixed output states.
        _cooler_on(pumps)
        _waste_on(pumps)

        peltier.off()

        laser_relay.on()
        laser_state["on"] = True

        start_time = ticks_ms()

        def status_func():
            rgb_values = _safe_get_latest(rgb_sensor)
            temp_values = _safe_get_latest(temperature)

            return {
                "available": True,
                "uptime_ms": ticks_diff(ticks_ms(), start_time),

                "system": {
                    "mode": "full live system test",
                    "dashboard": "running"
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
                    "cooler_pump_5v": _cooler_running(pumps),
                    "waste_pump_12v": _waste_running(pumps),

                    # Kept for the current simple dashboard table.
                    "water_pump": _cooler_running(pumps),
                    "spray_pump": _waste_running(pumps),

                    "peltier": peltier.running(),
                    "laser_relay": laser_state["on"]
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

        last_oled_update = ticks_ms()
        last_terminal_update = ticks_ms()
        last_laser_refresh = ticks_ms()

        oled.show_message(
            "Full Test",
            "System running",
            "Dashboard:",
            "192.168.4.1"
        )

        while True:
            now = ticks_ms()

            dashboard.update()

            rgb_values = rgb_sensor.update()
            temp_values = temperature.update()

            # Make sure both pumps stay ON all the time.
            if not _cooler_running(pumps):
                print("Cooler pump 5V was OFF. Turning back ON.")
                _cooler_on(pumps)

            if not _waste_running(pumps):
                print("Waste pump 12V was OFF. Turning back ON.")
                _waste_on(pumps)

            # Make sure Peltier stays OFF all the time.
            if peltier.running():
                print("Peltier was ON. Turning back OFF.")
                peltier.off()

            # Keep laser relay ON.
            # This refreshes the relay every second, similar to your old working test,
            # but without blocking the dashboard using time.sleep().
            if ticks_diff(now, last_laser_refresh) >= LASER_REFRESH_MS:
                last_laser_refresh = now
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
                    laser_state["on"]
                )

            sleep_ms(TIMING["main_loop_delay_ms"])

    except KeyboardInterrupt:
        print("Full live system test stopped manually.")

        if pumps is not None:
            _cooler_off(pumps)
            _waste_off(pumps)

        if peltier is not None:
            peltier.off()

        if laser_relay is not None:
            laser_relay.off()

        if oled is not None:
            oled.show_message(
                "Full Test",
                "Stopped",
                "Outputs OFF"
            )

        if dashboard is not None:
            dashboard.stop()

    except Exception as error:
        print("Full live system test crashed:", error)

        try:
            sys.print_exception(error)
        except Exception:
            pass

        if pumps is not None:
            _cooler_off(pumps)
            _waste_off(pumps)

        if peltier is not None:
            peltier.off()

        if laser_relay is not None:
            laser_relay.off()

        if oled is not None:
            oled.show_message(
                "Full Test",
                "CRASHED",
                "Outputs OFF"
            )

        if dashboard is not None:
            dashboard.stop()

        raise