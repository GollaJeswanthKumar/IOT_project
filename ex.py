import M5
from M5 import *
import time
import uhashlib
import binascii
import network
import ntptime
import urequests
from umqtt.simple import MQTTClient

M5.begin()

# ==================================
# WIFI CONFIGURATION
# ==================================

WIFI_SSID = "vivov27pro"
WIFI_PASSWORD = "sanjugolla"

SECRET_KEY = "MyIoTPass"

BASE_URL = "https://ambition-basil-smelting.ngrok-free.dev"

# MQTT Broker (Lab 4)
MQTT_BROKER = "192.168.1.100"   # your PC IP
MQTT_PORT = 1883
MQTT_TOPIC = b"bus/passenger_count"

IST_OFFSET = 19800


# ==================================
# WIFI CONNECTION
# ==================================

wlan = network.WLAN(network.STA_IF)

wlan.active(False)
time.sleep(1)

wlan.active(True)

wlan.connect(
    WIFI_SSID,
    WIFI_PASSWORD
)

print("Connecting WiFi...")

for _ in range(20):
    if wlan.isconnected():
        print(
            "Connected:",
            wlan.ifconfig()[0]
        )
        break

    time.sleep(1)


# ==================================
# NTP TIME SYNC
# ==================================

try:
    ntptime.settime()
    print("Time Synced")
except Exception as e:
    print("NTP Failed:", e)


# ==================================
# MQTT CONNECTION
# ==================================

mqtt = MQTTClient(
    "M5StackBusDevice",
    MQTT_BROKER,
    port=MQTT_PORT
)

mqtt.connect()

print("MQTT Connected")


# ==================================
# LOCAL IST TIME
# ==================================

def localtime_ist():
    return time.localtime(
        time.time() + IST_OFFSET
    )


# ==================================
# TOKEN GENERATION (20 sec)
# ==================================

def get_token():
    t = localtime_ist()

    slot = t[5] // 20

    time_str = "{}{}{}{}{}{}".format(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        slot
    )

    hash_obj = uhashlib.sha256(
        (SECRET_KEY + time_str).encode()
    )

    return binascii.hexlify(
        hash_obj.digest()
    ).decode()[:10]


# ==================================
# DISPLAY QR
# ==================================

def show_qr(url):

    Lcd.fillRect(
        0,
        0,
        320,
        220,
        0xFFFFFF
    )

    Widgets.QRCode(
        url,
        10,
        5,
        210,
        5
    )


# ==================================
# FETCH LIVE COUNT
# ==================================

def get_live_count():

    try:
        response = urequests.get(
            BASE_URL + "/get_count"
        )

        count = response.text.strip()

        response.close()

        return count

    except Exception as e:
        print("Fetch Error:", e)
        return "0"


# ==================================
# RESET SERVER COUNT
# ==================================

def reset_server_count():

    try:
        response = urequests.get(
            BASE_URL + "/reset_count"
        )

        print(
            "Server Reset:",
            response.text
        )

        response.close()

    except Exception as e:
        print("Reset Error:", e)


# ==================================
# MQTT PUBLISH
# ==================================

def publish_count(count):

    try:
        mqtt.publish(
            MQTT_TOPIC,
            str(count)
        )

        print(
            "Published MQTT:",
            count
        )

    except Exception as e:
        print(
            "MQTT Publish Error:",
            e
        )


# ==================================
# UI SETUP
# ==================================

Lcd.fillScreen(0xFFFFFF)

Lcd.fillRect(
    0,
    220,
    320,
    20,
    0x0078D7
)

clock_label = Widgets.Label(
    "00:00",
    0,
    222,
    1.0,
    0xFFFFFF,
    0x0078D7,
    Widgets.FONTS.DejaVu12
)

count_label = Widgets.Label(
    "Total: 0",
    200,
    222,
    1.0,
    0xFFFFFF,
    0x0078D7,
    Widgets.FONTS.DejaVu12
)


# ==================================
# INITIAL VALUES
# ==================================

last_slot = -1
last_fetch = 0
last_publish = time.time()


# ==================================
# INITIAL QR
# ==================================

token = get_token()

url = BASE_URL + "/enter?t=" + token

show_qr(url)

t = localtime_ist()

last_slot = t[5] // 20


# ==================================
# MAIN LOOP
# ==================================

while True:

    M5.update()

    t = localtime_ist()

    # Update clock
    clock_label.setText(
        "{:02d}:{:02d}".format(
            t[3],
            t[4]
        )
    )

    # QR refresh every 20 sec
    current_slot = t[5] // 20

    if current_slot != last_slot:

        token = get_token()

        url = BASE_URL + "/enter?t=" + token

        show_qr(url)

        print("QR Updated:", url)

        last_slot = current_slot


    # Fetch count every 5 sec
    if time.time() - last_fetch >= 5:

        count = get_live_count()

        count_label.setText(
            "Total: " + count
        )

        last_fetch = time.time()


    # Publish every 10 min
    if time.time() - last_publish >= 600:

        count = get_live_count()

        publish_count(count)

        reset_server_count()

        last_publish = time.time()


    time.sleep(1)