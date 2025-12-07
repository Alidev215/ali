from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import csv, os

app = Flask(__name__)

DATA_FILE = "data.csv"

# مسیر فایل داده را اگر وجود ندارد بساز
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Date", "Time", "Temperature", "Humidity"])

# تابع زمان ایران (+3:30)
def get_iran_time():
    utc_now = datetime.utcnow()
    iran_time = utc_now + timedelta(hours=3, minutes=30)
    return iran_time.strftime("%Y-%m-%d"), iran_time.strftime("%H:%M:%S")

@app.route("/")
def home():
    return "<h3>✅ Flask Server is Running - ESP32 Project</h3><a href='/dashboard'>Go to Dashboard</a>"

@app.route("/data", methods=["POST"])
def data():
    temp = request.form.get("temperature")
    hum = request.form.get("humidity")

    date, time = get_iran_time()

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, time, temp, hum])

    print(f"✅ {date} {time} | Temp: {temp} °C | Hum: {hum} %")
    return "Data saved successfully"

@app.route("/get_data")
def get_data():
    data = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return jsonify(data)

# پاک کردن تمام داده‌ها (CSV ریست میشه)
@app.route('/clear_data', methods=['POST'])
def clear_data():
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['Date', 'Time', 'Temperature', 'Humidity'])
    return jsonify({"message": "✅ تمام داده‌ها با موفقیت حذف شدند"})

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

# داشبورد (Dark Mode)
@app.route("/dashboard")
def dashboard():
    return render_template_string("""
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
        canvas {
            background-color: #1e1e2f;
            border-radius: 10px;
            padding: 10px;
        }
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
        .btn.danger:hover { background-color: #c9302c; }
        table {
            margin: 20px auto;
            border-collapse: collapse;
            width: 70%;
        }
        th, td {
            border: 1px solid #444;
            padding: 8px;
        }
    </style>
</head>
<body>
    <h1>📊 داشبورد آنلاین ESP32</h1>
    <button class="btn on" onclick="toggleLED('on')">روشن کردن LED 💡</button>
    <button class="btn off" onclick="toggleLED('off')">خاموش کردن LED 💤</button>
    <button class="btn danger" onclick="clearData()">🗑 پاک کردن داده‌ها</button>

    <canvas id="tempChart" width="400" height="180"></canvas>
    <canvas id="humChart" width="400" height="180"></canvas>

    <h3>📅 آخرین مقادیر دریافتی</h3>
    <table id="dataTable">
        <thead><tr><th>تاریخ</th><th>ساعت</th><th>دما (°C)</th><th>رطوبت (%)</th></tr></thead>
        <tbody></tbody>
    </table>

    <script>
        const tempCtx = document.getElementById('tempChart').getContext('2d');
        const humCtx = document.getElementById('humChart').getContext('2d');

        const tempChart = new Chart(tempCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'دما (°C)', borderColor: '#FF9800', data: [], fill: false }] },
            options: { scales: { y: { beginAtZero: true } } }
        });

        const humChart = new Chart(humCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'رطوبت (%)', borderColor: '#03A9F4', data: [], fill: false }] },
            options: { scales: { y: { beginAtZero: true } } }
        });

        async function updateCharts() {
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

            const tableBody = document.querySelector('#dataTable tbody');
            tableBody.innerHTML = '';
            data.slice(-10).reverse().forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${row.Date}</td><td>${row.Time}</td><td>${row.Temperature}</td><td>${row.Humidity}</td>`;
                tableBody.appendChild(tr);
            });
        }

        async function toggleLED(state) {
            await fetch(`/led/${state}`, { method: 'POST' });
            alert(state === 'on' ? "💡 LED روشن شد" : "💤 LED خاموش شد");
        }

        async function clearData() {
            if (confirm("آیا مطمئنی می‌خوای تمام داده‌ها حذف بشن؟")) {
                const res = await fetch('/clear_data', { method: 'POST' });
                const result = await res.json();
                alert(result.message);
                await updateCharts();
            }
        }

        updateCharts();
        setInterval(updateCharts, 600000); // هر 10 دقیقه
    </script>
</body>
</html>
""")

# ران در حالت محلی
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
