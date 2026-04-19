from flask import Flask, request
import hashlib
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# CONFIGURATION
SECRET_KEY = "MyIoTPass"
passenger_count = 0
used_tokens = set()

IST = timezone(timedelta(hours=5, minutes=30))

def get_expected_hash():
    t = datetime.now(IST)
    time_str = f"{t.year}{t.month}{t.day}{t.hour}{t.minute}"
    return hashlib.sha256((SECRET_KEY + time_str).encode()).hexdigest()[:10]

@app.route('/enter')
def enter():
    global passenger_count
    token = request.args.get('t')

    if not token:
        return "<h1>Invalid QR</h1><p>No token provided.</p>", 403

    expected_hash = get_expected_hash()

    if token == expected_hash:
        passenger_count += 1
        return f"<h1>Entry Successful!</h1><p>Current Count: {passenger_count}</p>"
    else:
        return "<h1>Invalid QR</h1><p>Code expired or incorrect.</p>", 403

@app.route('/get_count')
def get_count():
    global passenger_count
    return str(passenger_count)

@app.route('/debug')
def debug():
    t = datetime.now(IST)
    time_str = f"{t.year}{t.month}{t.day}{t.hour}{t.minute}"
    token = hashlib.sha256((SECRET_KEY + time_str).encode()).hexdigest()[:10]
    return f"<p>Expected token: <b>{token}</b></p><p>Time used: {time_str}</p><p>IST: {t}</p>"

@app.route('/')
def health():
    return {
        "status": "ok",
        "message": "Flask server is running",
        "passenger_count": passenger_count
    }

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)