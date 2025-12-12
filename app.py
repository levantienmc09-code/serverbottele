import telebot
import requests
import os
import threading
from flask import Flask

BOT_TOKEN = "8400775347:AAHruoy1eurSYRM7WvUhqPQ7q32xWlT268c"
API_KEY = "apikeysumi"
API_URL = "https://adidaphat.site/facebook/getinfo"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Flask app cực đơn giản
app = Flask(__name__)

def get_info(uid):
    try:
        res = requests.get(f"{API_URL}?uid={uid}&apikey={API_KEY}", timeout=10)
        return res.json() if res.status_code == 200 else None
    except:
        return None

@bot.message_handler(commands=['idfb'])
def cmd_idfb(message):
    parts = message.text.split()
    uid = parts[1] if len(parts) > 1 else None
    
    if uid:
        process_uid(message, uid)
    else:
        bot.reply_to(message, "📝 Nhập UID:")
        bot.register_next_step_handler(message, lambda m: process_uid(m, m.text))

def process_uid(message, uid):
    uid = uid.strip()
    if not uid or uid.startswith('/'): return
    
    data = get_info(uid)
    if not data or "name" not in data:
        bot.send_message(message.chat.id, f"❌ Không tìm thấy UID: `{uid}`")
        return
    
    # Xử lý created_time
    created_time = data.get('created_time', 'N/A')
    if isinstance(created_time, str):
        created_time = created_time.replace('||', ' | ')
    
    # Xử lý love
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
        bot.send_photo(message.chat.id, data['avatar'], caption=f"🖼️ {data['name']}")

def get_work_info(data):
    if not data.get('work'):
        return "Không có thông tin"
    jobs = []
    for job in data['work'][:2]:
        if isinstance(job, dict):
            emp = job.get('employer', {})
            if isinstance(emp, dict):
                emp = emp.get('name', '')
            else:
                emp = ''
            
            pos = job.get('position', {})
            if isinstance(pos, dict):
                pos = pos.get('name', '')
            else:
                pos = ''
                
            if emp or pos:
                jobs.append(f"{pos} tại {emp}" if pos and emp else emp or pos)
    return "\n".join(jobs) if jobs else "Không có thông tin"

@bot.message_handler(commands=['start', 'help'])
def cmd_help(message):
    bot.send_message(message.chat.id, 
        "🤖 *FB Check Bot*\n\n"
        "`/idfb [UID]` - Check TT FB\n"
        "Ví dụ: `/idfb 1`")

@bot.message_handler(func=lambda m: m.text and m.text.strip().isdigit())
def handle_direct_uid(message):
    process_uid(message, message.text.strip())

# Route đơn giản chỉ để Render biết app đang chạy
@app.route('/')
def home():
    return "🤖 FB Check Bot đang chạy... (Bot Telegram)"

@app.route('/health')
def health_check():
    return 'OK'

# Chạy bot trong thread riêng
def run_bot():
    print("🤖 Bot đang chạy...")
    bot.infinity_polling()

if __name__ == "__main__":
    # Start bot thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
