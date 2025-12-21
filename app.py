import telebot
import requests
import os
import threading
import time
from flask import Flask, render_template_string

# ===== CONFIG =====
BOT_TOKEN = "8540830463:AAGaLsA7OgrmWSOSg43xowpO3ZBXspyUtcM"
API_KEY = "apikeysumi"
API_URL = "https://adidaphat.site/facebook/getinfo"
SELF_URL = "https://checkttfbtele.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# ===== DATA =====
BOT_NAME = "Unknown"
command_logs = []

# ===== INIT BOT INFO =====
def init_bot_info():
    global BOT_NAME
    try:
        BOT_NAME = bot.get_me().first_name
    except:
        BOT_NAME = "Telegram Bot"

def log_user(message, command):
    command_logs.insert(0, {
        "name": message.from_user.full_name,
        "command": command
    })
    if len(command_logs) > 50:
        command_logs.pop()

# ===== API FB =====
def get_info(uid):
    try:
        r = requests.get(
            f"{API_URL}?uid={uid}&apikey={API_KEY}",
            timeout=10
        )
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print("API ERROR:", e)
        return None

# ===== BOT HANDLERS =====
@bot.message_handler(commands=['start', 'help'])
def cmd_help(message):
    log_user(message, message.text)
    bot.send_message(
        message.chat.id,
        "🤖 *FB Check Bot*\n\n"
        "`/idfb [UID]` - Check TT Facebook\n"
        "Ví dụ: `/idfb 1`"
    )

@bot.message_handler(commands=['idfb'])
def cmd_idfb(message):
    log_user(message, message.text)
    parts = message.text.split()
    uid = parts[1] if len(parts) > 1 else None

    if uid:
        process_uid(message, uid)
    else:
        bot.reply_to(message, "📝 Nhập UID:")
        bot.register_next_step_handler(
            message, lambda m: process_uid(m, m.text)
        )

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit())
def handle_uid(message):
    log_user(message, message.text)
    process_uid(message, message.text.strip())

def process_uid(message, uid):
    threading.Thread(
        target=process_uid_async,
        args=(message, uid),
        daemon=True
    ).start()

def process_uid_async(message, uid):
    uid = uid.strip()
    data = get_info(uid)

    if not data or "name" not in data:
        bot.send_message(message.chat.id, f"❌ Không tìm thấy UID: `{uid}`")
        return

    created_time = data.get("created_time", "N/A")
    if isinstance(created_time, str):
        created_time = created_time.replace("||", " | ")

    love_info = "Không có"
    love = data.get("love")
    if isinstance(love, dict) and love.get("name"):
        love_info = love["name"]

    result = (
        f"📘 THÔNG TIN FACEBOOK\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Tên: {data.get('name')}\n"
        f"🔗 Profile: {data.get('link_profile')}\n"
        f"🆔 UID: {data.get('uid', uid)}\n"
        f"📛 Username: @{data.get('username', 'Không có')}\n"
        f"📅 Tạo tài khoản: {created_time}\n"
        f"🎂 Sinh nhật: {data.get('birthday', 'N/A')}\n"
        f"⚤ Giới tính: {data.get('gender', 'N/A')}\n"
        f"💞 Mối quan hệ: {data.get('relationship_status', 'Không có')}\n"
        f"❤️ Người yêu: {love_info}\n"
        f"📊 Người theo dõi: {data.get('follower', 'Không công khai')}\n"
        f"✅ Tích xanh: {'✅ Có' if data.get('tichxanh') else '❌ Không'}\n"
        f"📍 Địa điểm: {data.get('location', 'Không có')}\n"
        f"🏠 Quê quán: {data.get('hometown', 'Không có')}\n"
        f"💼 Công việc:\n{get_work_info(data)}\n"
        f"📝 Giới thiệu:\n{data.get('about', 'Không có')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Bot by FBCheck"
    )

    bot.send_message(message.chat.id, result, disable_web_page_preview=True)

    if data.get("avatar"):
        bot.send_photo(
            message.chat.id,
            data["avatar"],
            caption=f"🖼️ {data.get('name')}"
        )

def get_work_info(data):
    if not data.get("work"):
        return "Không có thông tin"
    jobs = []
    for job in data["work"][:2]:
        emp = job.get("employer", {})
        pos = job.get("position", {})
        emp = emp.get("name", "") if isinstance(emp, dict) else ""
        pos = pos.get("name", "") if isinstance(pos, dict) else ""
        if emp or pos:
            jobs.append(f"{pos} tại {emp}" if pos and emp else emp or pos)
    return "\n".join(jobs) if jobs else "Không có thông tin"

# ===== WEB UI (MOBILE FRIENDLY) =====
HTML = """
<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bot Dashboard</title>
<style>
body{margin:0;font-family:system-ui;background:#0f172a;color:#e5e7eb}
.container{padding:16px;max-width:720px;margin:auto}
.card{background:#020617;border-radius:14px;padding:16px;margin-bottom:16px}
h1{font-size:20px;color:#22c55e;margin:0 0 10px}
h2{font-size:16px;color:#38bdf8;margin:0 0 10px}
.table{width:100%;border-collapse:collapse;font-size:14px}
.table td{padding:8px 6px;border-bottom:1px solid #1e293b;word-break:break-word}
.badge{display:inline-block;padding:4px 10px;border-radius:999px;background:#16a34a;font-size:12px}
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>🤖 {{ bot_name }}</h1>
    <span class="badge">RUNNING</span>
  </div>

  <div class="card">
    <h2>📊 Người dùng gần đây</h2>
    <table class="table">
      {% for log in logs %}
      <tr>
        <td><b>{{ log.name }}</b><br><small>{{ log.command }}</small></td>
      </tr>
      {% endfor %}
    </table>
  </div>
</div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(
        HTML,
        bot_name=BOT_NAME,
        logs=command_logs
    )

@app.route("/health")
def health():
    return "OK"

# ===== AUTO SELF PING (15s) =====
def auto_ping():
    while True:
        try:
            requests.get(SELF_URL, timeout=5)
            print("PING OK")
        except Exception as e:
            print("PING ERROR:", e)
        time.sleep(15)

# ===== RUN =====
def run_bot():
    init_bot_info()
    while True:
        try:
            print("🤖 Bot polling...")
            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )
        except Exception as e:
            print("BOT CRASH:", e)
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    threading.Thread(target=auto_ping, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
