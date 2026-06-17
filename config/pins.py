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
        "addr": "0x3C",
    },

    # 5V water pump using L9110S
    "water_pump": {
        "a1": 18,
        "a2": 19,
    },

    # 12V diaphragm spray pump using L298
    "spray_pump": {
        "ina": 25,
        "inb": 26,
    },

    # Peltier relay module
    "peltier": {
        "relay": 32,
    },

    # laser relay module
    "laser": {
        "relay-1": 33,
        "relay-2": 27,
    }
}