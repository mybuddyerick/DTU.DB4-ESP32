from time import sleep_ms, ticks_ms, ticks_diff
import sys

from control.rgb_sensor import RGBSensorControl
from control.temperature import TemperatureControl
from control.oled_display import OLEDDisplay
from control.pumps import PumpsControl
from control.peltier import PeltierControl

# Allow importing /site/hosting.py
sys.path.append("/site")
from hosting import WebServer


def run(config):
    pins = config["pins"]
    paths = config["paths"]
    timing = config["timing"]

    latest_rgb = None
    latest_temp = None

    print("Starting general DB4 system instructions...")

    # -----------------------------
    # OLED
    # -----------------------------

    oled = OLEDDisplay(
        sda_pin=pins["OLED_SDA_PIN"],
        scl_pin=pins["OLED_SCL_PIN"],
        addr=pins["OLED_ADDR"]
    )

    try:
        oled.show_message(
            "DB4 Starting",
            "Loading system",
            "Please wait"
        )
    except Exception:
        pass

    # -----------------------------
    # Web server
    # -----------------------------

    print()
    print("=== WEB SERVER SETUP ===")

    web_server = None

    try:
        web_server = WebServer(
            port=80,
            latest_rgb_func=lambda: latest_rgb
        )

        web_server.start()
        print("Web server started.")

    except Exception as error:
        print("Web server setup failed:", error)

    # -----------------------------
    # RGB logger
    # -----------------------------

    print()
    print("=== RGB SENSOR SETUP ===")

    rgb_sensor = RGBSensorControl(
        csv_path=paths["RGB_CSV_PATH"],
        interval_ms=timing["RGB_LOG_INTERVAL_MS"],
        sda_pin=pins["RGB_SDA_PIN"],
        scl_pin=pins["RGB_SCL_PIN"],
        led_pin=pins["RGB_LED_PIN"],
        verbose=True
    )

    rgb_sensor.led_off()

    # -----------------------------
    # Temperature logger
    # -----------------------------

    print()
    print("=== TEMPERATURE SETUP ===")

    temperature = TemperatureControl(
        csv_path=paths["TEMP_CSV_PATH"],
        interval_ms=timing["TEMP_LOG_INTERVAL_MS"],
        adc_pin=pins["TEMP_SENSOR_PIN"],
        verbose=True
    )

    # -----------------------------
    # Outputs
    # -----------------------------
    # These are initialized but not automatically activated.
    # Specific experiments should decide when to use them.

    print()
    print("=== OUTPUT SETUP ===")

    pumps = PumpsControl(
        water_pin_a=pins["WATER_PUMP_A1"],
        water_pin_b=pins["WATER_PUMP_A2"],
        spray_pin_a=pins["SPRAY_PUMP_INA"],
        spray_pin_b=pins["SPRAY_PUMP_INB"]
    )

    peltier = PeltierControl(
        relay_pin=pins["PELTIER_RELAY_PIN"]
    )

    pumps.water_off()
    pumps.spray_off()
    peltier.off()

    print()
    print("=== SYSTEM LOOP STARTED ===")
    print("Web dashboard: http://192.168.4.1/")
    print("RGB CSV:", paths["RGB_CSV_PATH"])
    print("Temperature CSV:", paths["TEMP_CSV_PATH"])
    print("Outputs are initialized but not running automatically.")
    print()

    try:
        oled.show_message(
            "DB4 Running",
            "Loggers active",
            "Outputs idle"
        )
    except Exception:
        pass

    now = ticks_ms()
    last_oled_update = now

    while True:
        now = ticks_ms()

        # Hosting
        if web_server is not None:
            web_server.update()

        # Sensor loggers
        latest_rgb = rgb_sensor.update()
        latest_temp = temperature.update()

        # Keep RGB sensor LED off
        rgb_sensor.led_off()

        # OLED status update
        if ticks_diff(now, last_oled_update) >= timing["OLED_UPDATE_INTERVAL_MS"]:
            last_oled_update = now

            oled.update(
                rgb_values=latest_rgb,
                temp_values=latest_temp,
                pumps=pumps,
                peltier=peltier
            )

        # Keep output timing systems updated,
        # but do not start any output automatically.
        pumps.update()
        peltier.update()

        sleep_ms(timing["MAIN_LOOP_DELAY_MS"])