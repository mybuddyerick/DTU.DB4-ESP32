# import network
# import time

# def setup_access_point():
#     # 1. Turn OFF station mode (so it stops searching for external routers)
#     sta_if = network.WLAN(network.STA_IF)
#     sta_if.active(False)
    
#     # 2. Turn ON Access Point mode (so the ESP32 broadcasts its own signal)
#     ap_if = network.WLAN(network.AP_IF)
#     ap_if.active(True)
    
#     # 3. Configure the ESP32's local network settings
#     # ESSID = Network Name, Authmode 3 = WPA2 Security
#     ap_if.config(essid="group-13-ESP32", password="group13dtu", authmode=3)
    
#     print("ESP32 Wi-Fi Access Point is Active!")
#     # By default, MicroPython Access Points always assign themselves the IP: 192.168.4.1
#     print("Network Configuration:", ap_if.ifconfig())

# # Run the network creator
# setup_access_point()