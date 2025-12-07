from flask import Flask, request, jsonify, render_template_string
import csv, os, json
from datetime import datetime

app = Flask(__name__)

DATA_FILE = 'data.csv'
STATUS_FILE = 'status.json'  # فایل ذخیره وضعیت LED

# 🔹 اگر فایل CSV وجود ندارد، ایجادش کن
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['Date', 'Time', 'Temperature', 'Humidity'])

# 🔹 بارگزاری یا مقداردهی اولیه وضعیت LED
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r') as f:
        try:
            led_status = json.load(f).get('led', False)
        except Exception:
            led_status = False
else:
    led_status = False

# 🏠 صفحه‌ی اصلی سرور
@app.route('/')
def home():
    return "✅ ESP32 Cloud Server is running!"

# 📩 دریافت داده از ESP32 (دما و رطوبت)
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.get_json(force=True)
    now = datetime.now()
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            data.get('temperature'),
            data.get('humidity')
        ])
    return jsonify({"message": "Data received"}), 200

# 📊 ارسال داده‌ها برای نمودارها
@app.route('/get_data')
def get_data():
    result = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            result.append(r)
    return jsonify(result)

# ⚙️ وضعیت فعلی LED (برای ESP32)
@app.route('/get_led_status')
def get_led_status():
    return jsonify({"led": led_status})

# 🎛 دکمه روشن/خاموش LED (از مرورگر یا ESP)
@app.route('/toggle_led', methods=['GET', 'POST'])
def toggle_led():
    global led_status
    led_status = not led_status
    with open(STATUS_FILE, 'w') as f:
        json.dump({"led": led_status}, f)
    return jsonify({"led": led_status})

# 🌡 داشبورد زنده با نمودارها و کنترل LED
@app.route('/dashboard')
def dashboard():
    html = """
    <html>
    <head>
      <title>ESP32 Dashboard - Cloud Control</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body {
          font-family: 'Segoe UI', sans-serif;
          background-color: #f8f9fa;
          text-align: center;
          margin-top: 40px;
        }
        h1 { color: #333; }
        .btn {
          background: #0078d7; color: white;
          border: none; padding: 10px 30px; border-radius: 8px;
          cursor: pointer; font-size: 16px; margin-bottom: 20px;
          transition: background-color 0.3s ease;
        }
        .btn.on { background: #d9534f; }
        canvas { margin: 20px auto; display: block; }
        footer { margin-top: 40px; color: #666; font-size: 14px; }
      </style>
    </head>
    <body>
      <h1>ESP32 💡 Live Dashboard + LED Control</h1>
      <button id="ledBtn" class="btn" onclick="toggleLED()">Toggle LED</button>

      <div>
        <canvas id="tempChart" width="600" height="250"></canvas>
        <canvas id="humChart" width="600" height="250"></canvas>
      </div>

      <footer>Made with ❤️ by Alldev215</footer>

      <script>
      async function fetchData(){
          const res = await fetch('/get_data');
          return res.json();
      }

      async function fetchLED(){
          const res = await fetch('/get_led_status');
          const state = await res.json();
          const btn = document.getElementById('ledBtn');
          btn.textContent = state.led ? 'LED is ON - Click to turn OFF' : 'LED is OFF - Click to turn ON';
          btn.className = state.led ? 'btn on' : 'btn';
      }

      async function toggleLED(){
          await fetch('/toggle_led', { method: 'POST' });
          await fetchLED();
      }

      async function updateCharts(){
          const data = await fetchData();
          const times = data.map(r => r.Time);
          const temps = data.map(r => parseFloat(r.Temperature));
          const hums = data.map(r => parseFloat(r.Humidity));

          tempChart.data.labels = times;
          tempChart.data.datasets[0].data = temps;
          tempChart.update();

          humChart.data.labels = times;
          humChart.data.datasets[0].data = hums;
          humChart.update();
      }

      const tempChart = new Chart(document.getElementById('tempChart'), {
          type: 'line',
          data: {
              labels: [],
              datasets: [{
                  label: 'Temperature (°C)',
                  borderColor: '#ff5733',
                  backgroundColor: 'rgba(255,87,51,0.2)',
                  data: []
              }]
          },
          options: { scales: { y: { beginAtZero: false } } }
      });

      const humChart = new Chart(document.getElementById('humChart'), {
          type: 'line',
          data: {
              labels: [],
              datasets: [{
                  label: 'Humidity (%)',
                  borderColor: '#0078d7',
                  backgroundColor: 'rgba(0,120,215,0.2)',
                  data: []
              }]
          },
          options: { scales: { y: { beginAtZero: false } } }
      });

      setInterval(updateCharts, 5000);
      setInterval(fetchLED, 5000);
      updateCharts();
      fetchLED();
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

# 🚀 اجرای سرور
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
