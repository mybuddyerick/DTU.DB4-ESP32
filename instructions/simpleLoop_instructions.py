# instructions/simpleLoop_instructions.py
#
# Simple loop experiment:
# - record temperature
# - keep both pumps always active
# - keep Peltier ON until temperature reaches 17 C
# - show status on OLED

from time import sleep_ms, ticks_ms, ticks_diff

from control.temperature import TemperatureControl
from control.oled_display import OLEDDisplay
from control.pumps import PumpsControl
from control.peltier import PeltierControl


TARGET_TEMP_C = 17.0


def run(config):
    pins = config["pins"]
    paths = config["paths"]
    timing = config["timing"]

    latest_temp = None

    print()
    print("====================================")
    print(" SIMPLE LOOP INSTRUCTIONS")
    print("====================================")
    print("Target temperature:", TARGET_TEMP_C, "C")
    print("5V pump: always ON")
    print("12V pump: always ON")
    print("Peltier: ON until temperature <= 17 C")
    print()

    # -----------------------------
    # OLED
    # -----------------------------

    oled = OLEDDisplay(
        sda_pin=pins["OLED_SDA_PIN"],
        scl_pin=pins["OLED_SCL_PIN"],
        addr=pins["OLED_ADDR"]
    )

    oled.show_message(
        "Simple Loop",
        "Starting...",
        "Target: 17 C"
    )

    # -----------------------------
    # Temperature logger
    # -----------------------------

    temperature = TemperatureControl(
        csv_path=paths["TEMP_CSV_PATH"],
        interval_ms=timing["TEMP_LOG_INTERVAL_MS"],
        adc_pin=pins["TEMP_SENSOR_PIN"],
        verbose=True
    )

    # -----------------------------
    # Pumps
    # -----------------------------

    pumps = PumpsControl(
        water_pin_a=pins["WATER_PUMP_A1"],
        water_pin_b=pins["WATER_PUMP_A2"],
        spray_pin_a=pins["SPRAY_PUMP_INA"],
        spray_pin_b=pins["SPRAY_PUMP_INB"]
    )

    # Both pumps should stay active during this instruction loop
    pumps.water_on()
    pumps.spray_on()

    # -----------------------------
    # Peltier
    # -----------------------------

    peltier = PeltierControl(
        relay_pin=pins["PELTIER_RELAY_PIN"]
    )

    # Start cooling immediately
    peltier.on()

    print()
    print("=== SIMPLE LOOP STARTED ===")
    print("Temperature CSV:", paths["TEMP_CSV_PATH"])
    print()

    oled.show_message(
        "Simple Loop",
        "Pumps: ON",
        "Peltier: ON"
    )

    last_oled_update = ticks_ms()

    try:
        while True:
            now = ticks_ms()

            # -----------------------------
            # Temperature logging
            # -----------------------------

            latest_temp = temperature.update()

            # -----------------------------
            # Keep pumps always ON
            # -----------------------------

            if not pumps.water_running():
                pumps.water_on()

            if not pumps.spray_running():
                pumps.spray_on()

            # -----------------------------
            # Peltier temperature control
            # -----------------------------

            if latest_temp is not None:
                temp_c = latest_temp["temp_c"]

                if temp_c <= TARGET_TEMP_C:
                    if peltier.running():
                        print("Target reached. Turning Peltier OFF.")
                        peltier.off()
                else:
                    if not peltier.running():
                        print("Temperature above target. Turning Peltier ON.")
                        peltier.on()

            # -----------------------------
            # OLED update
            # -----------------------------

            if ticks_diff(now, last_oled_update) >= timing["OLED_UPDATE_INTERVAL_MS"]:
                last_oled_update = now

                oled.update(
                    rgb_values=None,
                    temp_values=latest_temp,
                    pumps=pumps,
                    peltier=peltier
                )

            # -----------------------------
            # Update outputs
            # -----------------------------

            pumps.update()
            peltier.update()

            sleep_ms(timing["MAIN_LOOP_DELAY_MS"])

    except KeyboardInterrupt:
        print("Simple loop stopped manually.")
        print("Turning outputs OFF for safety.")

        pumps.water_off()
        pumps.spray_off()
        peltier.off()

        oled.show_message(
            "Loop stopped",
            "Outputs OFF"
        )