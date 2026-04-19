import M5
from M5 import *
import time
import uhashlib
import binascii
import network
import ntptime
import urequests

M5.begin()

# WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('vivov27pro', 'sanjugolla')

print("Connecting to WiFi...")
for _ in range(20):
    if wlan.isconnected():
        print("Connected! IP:", wlan.ifconfig()[0])
        break
    time.sleep(1)
else:
    print("WiFi Failed to Connect")

# NTP
try:
    ntptime.settime()
    print("Time synced via NTP")
except Exception as e:
    print("NTP sync failed:", e)

IST_OFFSET = 19800

def localtime_ist():
    return time.localtime(time.time() + IST_OFFSET)

SECRET_KEY = "MyIoTPass"
BASE_URL = "https://ambition-basil-smelting.ngrok-free.dev"

def get_token():
    t = localtime_ist()
    time_str = "{}{}{}{}{}".format(t[0], t[1], t[2], t[3], t[4])
    hash_obj = uhashlib.sha256((SECRET_KEY + time_str).encode())
    return binascii.hexlify(hash_obj.digest()).decode()[:10]

def show_qr(url):
    # Redraw white background to clear old QR
    Lcd.fillRect(0, 0, 320, 220, 0xFFFFFF)
    # Create a brand new QR widget with the URL
    Widgets.QRCode(url, 10, 5, 210, 5)

# --- Build UI ---
Lcd.fillScreen(0xFFFFFF)
Lcd.fillRect(0, 220, 320, 20, 0x0078D7)
clock_label = Widgets.Label("00:00", 0, 222, 1.0, 0xFFFFFF, 0x0078D7, Widgets.FONTS.DejaVu12)
count_label = Widgets.Label("Total: 0", 200, 222, 1.0, 0xFFFFFF, 0x0078D7, Widgets.FONTS.DejaVu12)

last_min = -1
last_fetch_time = 0

def update_count_from_server():
    global last_fetch_time
    if time.time() - last_fetch_time < 5:
        return
    try:
        url = BASE_URL + "/get_count"
        response = urequests.get(url)
        if response.status_code == 200:
            count = response.text.strip()
            print("Passenger count:", count)
            count_label.setText("Total: " + count)
        response.close()
        last_fetch_time = time.time()
    except Exception as e:
        print("ERROR:", e)
        count_label.setText("Offline")

# Generate QR immediately on startup
token = get_token()
new_url = BASE_URL + "/enter?t=" + token
show_qr(new_url)
last_min = localtime_ist()[4]
print("Initial QR URL:", new_url)

# Main Loop
while True:
    M5.update()
    t = localtime_ist()

    clock_label.setText("{:02d}:{:02d}".format(t[3], t[4]))

    if t[4] != last_min:
        token = get_token()
        new_url = BASE_URL + "/enter?t=" + token
        show_qr(new_url)
        print("Updated QR URL:", new_url)
        last_min = t[4]

    update_count_from_server()
    time.sleep(1)