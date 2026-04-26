import time
from flask import Flask, request
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ==================================
# CONFIGURATION
# ==================================

SECRET_KEY = "MyIoTPass"
passenger_count = 0
used_tokens = set()

IST = timezone(timedelta(hours=5, minutes=30))


# ==================================
# TOKEN GENERATION (20 sec validity)
# ==================================

def get_expected_hash():
    t = datetime.now(IST)

    # 20-second slot
    slot = t.second // 20

    time_str = f"{t.year}{t.month}{t.day}{t.hour}{t.minute}{slot}"

    return hashlib.sha256(
        (SECRET_KEY + time_str).encode()
    ).hexdigest()[:10]


# ==================================
# PASSENGER ENTRY API
# ==================================

@app.route('/enter')
def enter():
    global passenger_count

    token = request.args.get('t')

    if not token:
        return "<h1>Invalid QR</h1>", 403

    expected_hash = get_expected_hash()

    if token != expected_hash:
        return "<h1>QR Expired</h1>", 403

    # Device identification
    ip = request.remote_addr
    user_agent = request.headers.get(
        'User-Agent',
        'unknown'
    )

    language = request.headers.get(
        'Accept-Language',
        'unknown'
    )

    device_id = ip + "|" + user_agent + "|" + language

    scan_key = token + "|" + device_id

    # Prevent duplicate scan in same slot
    if scan_key in used_tokens:
        return "<h1>Already Scanned</h1>", 200

    used_tokens.add(scan_key)

    passenger_count += 1

    return (
        f"<h1>Entry Successful</h1>"
        f"<p>Count: {passenger_count}</p>"
    )


# ==================================
# GET CURRENT COUNT
# ==================================

@app.route('/get_count')
def get_count():
    global passenger_count
    return str(passenger_count)


# ==================================
# RESET COUNT (called by M5Stack)
# ==================================

@app.route('/reset_count')
def reset_count():
    global passenger_count
    global used_tokens

    passenger_count = 0
    used_tokens.clear()

    return "Reset Done"


# ==================================
# HEALTH CHECK
# ==================================

@app.route('/')
def health():
    return {
        "status": "running",
        "count": passenger_count
    }


# ==================================
# START SERVER
# ==================================

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000
    )