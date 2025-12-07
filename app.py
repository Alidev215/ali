from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import csv, os

app = Flask(__name__)

DATA_FILE = "data.csv"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(["Date", "Time", "Temperature", "Humidity", "Motion"])  # 💬 ستون جدید برای Motion

def get_iran_time():
    utc_now = datetime.utcnow()
    iran_time = utc_now + timedelta(hours=3, minutes=30)
    return iran_time.strftime("%Y-%m-%d"), iran_time.strftime("%H:%M:%S")

@app.route("/")
def home():
    return "<h3>✅ Flask Server is Running - ESP32 Project</h3><a href='/dashboard'>Go to Dashboard</a>"

# 💬 مسیر دریافت داده از ESP32
@app.route("/data", methods=["POST"])
def data():
    temp = request.form.get("temperature")
    hum = request.form.get("humidity")
    motion = request.form.get("motion", "0")  # 💬 اگر ارسال نشده بود پیش‌فرض ۰ باشه

    date, time = get_iran_time()

    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([date, time, temp, hum, motion])

    print(f"✅ {date} {time} | Temp: {temp}°C | Hum: {hum}% | Motion: {motion}")
    return "Data saved successfully"

@app.route("/get_data")
def get_data():
    data = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return jsonify(data)

@app.route('/clear_data', methods=['POST'])
def clear_data():
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(['Date', 'Time', 'Temperature', 'Humidity', 'Motion'])
    return jsonify({"message": "✅ تمام داده‌ها با موفقیت حذف شدند"})

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

@app.route("/get_led_status")
def get_led_status():
    return jsonify({"led": LED_STATE["status"]})

# 🔥 متغیر جدید برای کنترل نظارت حرکتی
MOTION_MONITOR = {"enabled": True, "last": 0}  # last = آخرین وضعیت دیده شده

@app.route("/motion/<state>", methods=["POST"])
def motion_control(state):
    if state.lower() == "on":
        MOTION_MONITOR["enabled"] = True
    elif state.lower() == "off":
        MOTION_MONITOR["enabled"] = False
    return jsonify(MOTION_MONITOR)

@app.route("/motion_status")
def motion_status():
    return jsonify(MOTION_MONITOR)

# 💻 Dashboard
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
.motion-box {
    margin: 20px auto;
    width: 50%;
    padding: 10px;
    border-radius: 8px;
    background: #1d1e2f;
}
.motion-active { color: #ff5252; font-weight: bold; }
.motion-inactive { color: #4caf50; }
</style>
</head>
<body>
<h1>📊 داشبورد آنلاین ESP32</h1>

<div>
    <button class="btn on" onclick="toggleLED('on')">روشن کردن LED 💡</button>
    <button class="btn off" onclick="toggleLED('off')">خاموش کردن LED 💤</button>
</div>

<div>
    <button class="btn on" onclick="toggleMotion('on')">✅ فعال‌سازی سنسور حرکت</button>
    <button class="btn off" onclick="toggleMotion('off')">⛔ غیرفعال کردن سنسور حرکت</button>
</div>

<button class="btn danger" onclick="clearData()">🗑 پاک کردن داده‌ها</button>

<div class="motion-box" id="motionBox">
    <h3>وضعیت حرکت:</h3>
    <p id="motionStatus" class="motion-inactive">در حال انتظار...</p>
</div>

<canvas id="tempChart"></canvas>
<canvas id="humChart"></canvas>

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
    const dataRes = await fetch('/get_data');
    const data = await dataRes.json();

    const labels = data.map(d => `${d.Date} ${d.Time}`);
    const temps = data.map(d => d.Temperature);
    const hums = data.map(d => d.Humidity);
    const motions = data.map(d => d.Motion);

    tempChart.data.labels = labels;
    tempChart.data.datasets[0].data = temps;
    humChart.data.labels = labels;
    humChart.data.datasets[0].data = hums;
    tempChart.update();
    humChart.update();

    // آخرین وضعیت حرکت
    const lastMotion = motions[motions.length - 1];
    const motionText = lastMotion === "1" ? "🚨 حرکت شناسایی شد!" : "✅ بدون حرکت";
    const motionElem = document.getElementById('motionStatus');
    motionElem.textContent = motionText;
    motionElem.className = lastMotion === "1" ? "motion-active" : "motion-inactive";
}

async function toggleLED(state) {
    await fetch(`/led/${state}`, {method:'POST'});
}
async function toggleMotion(state) {
    await fetch(`/motion/${state}`, {method:'POST'});
}
async function clearData() {
    if (confirm("آیا مطمئنی؟")) {
        await fetch('/clear_data', {method:'POST'});
        alert('✅ پاک شد');
        updateDashboard();
    }
}

updateDashboard();
setInterval(updateDashboard, 60000);
</script>
</body>
</html>
""")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
