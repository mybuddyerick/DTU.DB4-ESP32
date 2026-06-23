PINS = {
    # RGB sensor TCS34725
    "rgb": {
        "sda": 21,
        "scl": 22,
        "led": 23,
    },

    # Thermistor NTC 10k
    "temperature": {
        "adc": 34,
    },

    # OLED display
    "oled": {
        "sda": 4,
        "scl": 2,
        "addr": 0x3C,
    },

    # 12V pump using L298
    "cooler_pump": {
        "1": 25,
        "2": 26,
    },

    # You can power the motor side at 3.3V if the pump starts reliably.
    "waste_pump": {
        "1": 18,
        "2": 19,
    },

    # Peltier relay module
    "peltier": {
        "relay": 32,
    },

    # Laser relay module
    "laser": {
        "relay": 33,
    }
}
