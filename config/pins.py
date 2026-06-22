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

    # 5V cooler pump using L9110S
    "cooler_pump": {
        "1": 18,
        "2": 19,
    },

    # 12V waste pump using L298
    "waste_pump": {
        "1": 25,
        "2": 26,
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
