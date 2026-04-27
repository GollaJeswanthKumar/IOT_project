import time
from flask import Flask, request, jsonify, render_template_string
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

count_array = []
time_array = []

@app.route('/data', methods=['POST'])
def receive_data():
    global count_array
    global time_array

    data = request.get_json()
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON dictionary"}), 400

    for time_str, count in data.items():
        time_array.append(time_str)
        count_array.append(count)

    return jsonify({"status": "ok", "points_received": len(data)}), 200


@app.route('/data', methods=['GET'])
def data():
    global count_array
    global time_array

    html = render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Count Over Time</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0f1117;
      color: #e2e8f0;
      font-family: 'Courier New', monospace;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 40px 20px;
    }
    h1 {
      font-size: 1.4rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: #7ee8a2;
      margin-bottom: 8px;
    }
    p.subtitle {
      font-size: 0.75rem;
      color: #4a5568;
      letter-spacing: 0.1em;
      margin-bottom: 36px;
    }
    .chart-wrapper {
      width: 100%;
      max-width: 860px;
      background: #1a1d2e;
      border: 1px solid #2d3748;
      border-radius: 12px;
      padding: 32px;
      box-shadow: 0 0 40px rgba(126, 232, 162, 0.05);
    }
    canvas { width: 100% !important; }
    .no-data {
      color: #4a5568;
      font-size: 0.9rem;
      letter-spacing: 0.1em;
      padding: 60px 0;
      text-align: center;
    }
  </style>
</head>
<body>
  <h1>Live Count Monitor</h1>
  <p class="subtitle">POST to /data to stream new values</p>
  <div class="chart-wrapper">
    {% if time_array %}
    <canvas id="lineChart"></canvas>
    <script>
      const ctx = document.getElementById('lineChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: {{ time_array | tojson }},
          datasets: [{
            label: 'Count',
            data: {{ count_array | tojson }},
            borderColor: '#7ee8a2',
            backgroundColor: 'rgba(126, 232, 162, 0.08)',
            borderWidth: 2,
            pointBackgroundColor: '#7ee8a2',
            pointRadius: 5,
            pointHoverRadius: 7,
            tension: 0.35,
            fill: true,
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { labels: { color: '#a0aec0', font: { family: 'Courier New' } } },
            tooltip: {
              backgroundColor: '#1a1d2e',
              borderColor: '#7ee8a2',
              borderWidth: 1,
              titleColor: '#7ee8a2',
              bodyColor: '#e2e8f0',
            }
          },
          scales: {
            x: {
              ticks: { color: '#718096', font: { family: 'Courier New' } },
              grid: { color: '#2d3748' }
            },
            y: {
              ticks: { color: '#718096', font: { family: 'Courier New' } },
              grid: { color: '#2d3748' }
            }
          }
        }
      });
    </script>
    {% else %}
    <div class="no-data">[ no data yet — POST to /data to begin ]</div>
    {% endif %}
  </div>
</body>
</html>
    """, time_array=time_array, count_array=count_array)

    return html

# ==================================
# START SERVER
# ==================================

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000
    )