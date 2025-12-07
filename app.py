from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import csv, os

app = Flask(__name__)

DATA_FILE = "data.csv"

# اگر فایل داده وجود ندارد، هدر آن ایجاد شود
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Date", "Time", "Temperature", "Humidity"])

# تابع برای زمان ایران
def get_iran_time():
    utc_now = datetime.utcnow()
    iran_time = utc_now + timedelta(hours=3, minutes=30)
    return iran_time.strftime("%Y-%m-%d"), iran_time.strftime("%H:%M:%S")

# صفحه‌ی اصلی
@app.route("/")
def home():
    return "<h3>✅ Flask Server Running for ESP32</h3><a href='/dashboard'>Go to Dashboard</a>"

# دریافت داده از ESP32 (فرمت JSON)
@app.route("/data", methods=["POST"])
def data():
    data = request.get_json()
    temp = data.get("temperature")
    hum = data.get("humidity")

    date, time = get_iran_time()
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, time, temp, hum])

    print(f"✅ {date} {time} | Temp: {temp}°C | Humidity: {hum}%")
    return jsonify({"message": "Data saved successfully"})

# دریافت داده‌ها برای داشبورد
@app.route("/get_data")
def get_data():
    data = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return jsonify(data)

# حذف داده‌ها
@app.route("/clear_data", methods=["POST"])
def clear_data():
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Date", "Time", "Temperature", "Humidity"])
    return jsonify({"message": "✅ تمام داده‌ها حذف شدند"})

# وضعیت LED
LED_STATE = {"status": False}

@app.route("/led/<state>", methods=["POST"])
def led_control(state):
    if state.lower() == "on":
        LED_STATE["status"] = True
    elif state.lower() == "off":
        LED_STATE["status"] = False
    return jsonify(LED_STATE)

@app.route("/led_status")
def led_status():
    return jsonify(LED_STATE)

# داشبورد
@app.route("/dashboard")
def dashboard():
    html = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
      <meta charset="UTF-8">
      <title>ESP32 Dashboard</title>
      <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      <style>
        body {
          background-color: #0f1117;
          color: #fff;
          font-family: 'Vazirmatn', sans-serif;
          text-align: center;
          padding: 20px;
        }
        h1 { color: #4FC3F7; }
        .btn {
          margin: 6px;
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: bold;
        }
        .btn.on { background-color: #4CAF50; color: white; }
        .btn.off { background-color: #f44336; color: white; }
        .btn.danger { background-color: #d9534f; color: white; }
        table { margin:auto; border-collapse: collapse; width:80%; color:#EEE; }
        th, td { border:1px solid #555; padding:8px; }
        th { background:#222; }
        canvas {
          background-color: #1e1e2f;
          border-radius: 10px;
          padding: 10px;
          margin-top: 10px;
        }
      </style>
    </head>
    <body>
      <h1>📡 داشبورد آنلاین ESP32</h1>

      <div>
        <button class="btn on" onclick="toggleLED('on')">روشن کردن LED 💡</button>
        <button class="btn off" onclick="toggleLED('off')">خاموش کردن LED 💤</button>
        <button class="btn danger" onclick="clearData()">🗑 پاک کردن داده‌ها</button>
      </div>

      <canvas id="tempChart"></canvas>
      <canvas id="humChart"></canvas>

      <hr>
      <h3>📅 تاریخچه داده‌ها</h3>
      <table id="dataTable">
        <thead>
          <tr><th>تاریخ</th><th>زمان</th><th>دما (°C)</th><th>رطوبت (%)</th></tr>
        </thead>
        <tbody></tbody>
      </table>

      <script>
        const tempCtx = document.getElementById('tempChart').getContext('2d');
        const humCtx = document.getElementById('humChart').getContext('2d');

        const tempChart = new Chart(tempCtx, {
          type: 'line',
          data: { labels: [], datasets: [{ label: 'دما (°C)', borderColor: '#FF9800', data: [], fill: false }] },
        });
        const humChart = new Chart(humCtx, {
          type: 'line',
          data: { labels: [], datasets: [{ label: 'رطوبت (%)', borderColor: '#03A9F4', data: [], fill: false }] },
        });

        async function updateDashboard() {
          const res = await fetch('/get_data');
          const data = await res.json();

          const labels = data.map(d => `${d.Date} ${d.Time}`);
          const temps = data.map(d => d.Temperature);
          const hums = data.map(d => d.Humidity);

          tempChart.data.labels = labels;
          tempChart.data.datasets[0].data = temps;
          humChart.data.labels = labels;
          humChart.data.datasets[0].data = hums;
          tempChart.update();
          humChart.update();

          const tbody = document.querySelector("#dataTable tbody");
          tbody.innerHTML = "";
          data.slice(-20).reverse().forEach(d => {
              const row = `<tr><td>${d.Date}</td><td>${d.Time}</td><td>${d.Temperature}</td><td>${d.Humidity}</td></tr>`;
              tbody.insertAdjacentHTML("beforeend", row);
          });
        }

        async function toggleLED(state) {
          await fetch(`/led/${state}`, {method:'POST'});
        }
        async function clearData() {
          if (confirm("آیا مطمئنی برای حذف داده‌ها؟")) {
              await fetch('/clear_data', {method:'POST'});
              alert('✅ داده‌ها پاک شدند');
              updateDashboard();
          }
        }

        updateDashboard();
        setInterval(updateDashboard, 5000); // هر ۵ ثانیه رفرش
      </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
