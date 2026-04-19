from flask import Flask, request
import hashlib
import time

app = Flask(__name__)

# CONFIGURATION
SECRET_KEY = "MyIoTPass"
passenger_count = 0
used_tokens = set() # To prevent double-scanning

@app.route('/enter')
def enter():
    global passenger_count
    token = request.args.get('t')
    
    # Verification Logic
    t = time.localtime()
    time_str = f"{t.tm_year}{t.tm_mon}{t.tm_mday}{t.tm_hour}{t.tm_min}"
    expected_hash = hashlib.sha256((SECRET_KEY + time_str).encode()).hexdigest()[:10]

    # Check if valid
    if token == expected_hash:
        if token not in used_tokens:
            passenger_count += 1
            used_tokens.add(token)
            return f"<h1>Entry Successful!</h1><p>Current Count: {passenger_count}</p>"
        else:
            return "<h1>Already Scanned!</h1><p>This QR code was already used.</p>"
    else:
        return "<h1>Invalid QR</h1><p>Code expired or incorrect.</p>", 403

@app.route('/get_count')
def get_count():
    global passenger_count
    return str(passenger_count)

if __name__ == '__main__':
    # '0.0.0.0' allows other devices (phones) on your Wi-Fi to see the server
    app.run(host='0.0.0.0', port=5000)