import network
import time
import webrepl

AP_NAME = "group-13-ESP32"
AP_PASSWORD = "group13dtu"


def setup_access_point():
    # Disable station mode.
    # This stops the ESP32 from trying to connect to an external router.
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(False)

    # Enable access point mode.
    # This makes the ESP32 create its own Wi-Fi network.
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)

    # Configure ESP32 Wi-Fi network.
    # authmode=3 means WPA2 password protection.
    ap_if.config(
        essid=AP_NAME,
        password=AP_PASSWORD,
        authmode=3
    )

    # Give the AP a moment to start.
    time.sleep(1)

    print()
    print("====================================")
    print(" ESP32 ACCESS POINT STARTED")
    print("====================================")
    print("Network name:", AP_NAME)
    print("Password:", AP_PASSWORD)
    print("Open dashboard at: http://192.168.4.1")
    print("Network config:", ap_if.ifconfig())
    print()

    # Start WebREPL to allow Python REPL access over Wi-Fi
    try:
        webrepl.start()
        print("WebREPL started. Connect at http://micropython.org/webrepl/")
    except Exception as e:
        print("WebREPL failed to start:", e)

setup_access_point()