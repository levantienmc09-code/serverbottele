import telebot
import requests
import os
import threading
from flask import Flask, render_template_string

# ===== CONFIG =====
BOT_TOKEN = "8540830463:AAGaLsA7OgrmWSOSg43xowpO3ZBXspyUtcM"
API_KEY = "apikeysumi"
API_URL = "https://adidaphat.site/facebook/getinfo"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# ===== DATA =====
BOT_NAME = "Unknown"
command_logs = []

# ===== INIT BOT INFO =====
def init_bot_info():
    global BOT_NAME
    try:
        me = bot.get_me()
        BOT_NAME = me.first_name
    except Exception as e:
        print("BOT INFO ERROR:", e)

def log_user(message, command):
    command_logs.insert(0, {
        "name": message.from_user.full_name,
        "command": command
    })
    if len(command_logs) > 50:
        command_logs.pop()

# ===== API =====
def get_info(uid):
    try:
        res = requests.get(f"{API_URL}?uid={uid}&apikey={API_KEY}", timeout=10)
        return res.json() if res.status_code == 200 else None
    except Exception as e:
        print("API ERROR:", e)
        return None

# ===== BOT LOGIC (GIỮ NGUYÊN) =====
@bot.message_handler(commands=['idfb'])
def cmd_idfb(message):
    log_user(message, message.text)
    parts = message.text.split()
    uid = parts[1] if len(parts) > 1 else None

    if uid:
        process_uid(message, uid)
    else:
        bot.reply_to(message, "📝 Nhập UID:")
        bot.register_next_step_handler(message, lambda m: process_uid(m, m.text))

def process_uid(message, uid):
    uid = uid.strip()
    if not uid or uid.startswith('/'):
        return

    data = get_info(uid)
    if not data or "name" not in data:
        bot.send_message(message.chat.id, f"❌ Không tìm thấy UID: `{uid}`")
        return

    created_time = data.get('created_time', 'N/A')
    if isinstance(created_time, str):
        created_time = created_time.replace('||', ' | ')

    love_info = "Không có"
    love_data = data.get('love')
    if isinstance(love_data, dict):
        love_name = love_data.get('name', '')
        if love_name:
            love_info = love_name

    result = (
        f"📘 THÔNG TIN FACEBOOK\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Tên: {data.get('name', 'N/A')}\n"
        f"🔗 Profile: {data.get('link_profile', 'N/A')}\n"
        f"🆔 UID: {data.get('uid', uid)}\n"
        f"📛 Username: @{data.get('username', 'Không có')}\n"
        f"📅 Tạo tài khoản: {created_time}\n"
        f"🎂 Sinh nhật: {data.get('birthday', 'N/A')}\n"
        f"⚤ Giới tính: {data.get('gender', 'N/A')}\n"
        f"💞 Mối quan hệ: {data.get('relationship_status', 'Không có dữ liệu!')}\n"
        f"❤️ Người yêu: {love_info}\n"
        f"📊 Người theo dõi: {data.get('follower', 'Không công khai')}\n"
        f"✅ Tích xanh: {'✅ Có' if data.get('tichxanh') else '❌ Không'}\n"
        f"📍 Địa điểm: {data.get('location', 'Không có')}\n"
        f"🏠 Quê quán: {data.get('hometown', 'Không có')}\n"
        f"💼 Công việc:\n{get_work_info(data)}\n"
        f"📝 Giới thiệu:\n{data.get('about', 'Không có dữ liệu!')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Bot by FBCheck"
    )

    bot.send_message(message.chat.id, result, disable_web_page_preview=True)

    if data.get('avatar'):
        bot.send_photo(
            message.chat.id,
            data['avatar'],
            caption=f"🖼️ {data['name']}"
        )

def get_work_info(data):
    if not data.get('work'):
        return "Không có thông tin"
    jobs = []
    for job in data['work'][:2]:
        if isinstance(job, dict):
            emp = job.get('employer', {})
            emp = emp.get('name', '') if isinstance(emp, dict) else ''
            pos = job.get('position', {})
            pos = pos.get('name', '') if isinstance(pos, dict) else ''
            if emp or pos:
                jobs.append(f"{pos} tại {emp}" if pos and emp else emp or pos)
    return "\n".join(jobs) if jobs else "Không có thông tin"

@bot.message_handler(commands=['start', 'help'])
def cmd_help(message):
    log_user(message, message.text)
    bot.send_message(
        message.chat.id,
        "🤖 *FB Check Bot*\n\n"
        "`/idfb [UID]` - Check TT FB\n"
        "Ví dụ: `/idfb 1`"
    )

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit())
def handle_direct_uid(message):
    log_user(message, message.text)
    process_uid(message, message.text.strip())

# ===== WEB UI =====
HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Bot Dashboard</title>
<style>
body{background:#0f172a;color:#e5e7eb;font-family:Arial;padding:20px}
h1{color:#22c55e}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{padding:10px;border-bottom:1px solid #334155}
th{color:#38bdf8;text-align:left}
</style>
</head>
<body>
<h1>🤖 Bot đang chạy: {{ bot_name }}</h1>
<h2>📊 Lịch sử người dùng</h2>
<table>
<tr><th>User</th><th>Lệnh đã dùng</th></tr>
{% for log in logs %}
<tr><td>{{ log.name }}</td><td>{{ log.command }}</td></tr>
{% endfor %}
</table>
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

# ===== RUN =====
def run_bot():
    init_bot_info()
    print("🤖 Bot đang polling Telegram...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)