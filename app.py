from flask import Flask, request, render_template_string, redirect, session, url_for
import os, hashlib, subprocess, json, re, requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Folder lưu user & bot (relative) ---
ROOT_DIR = os.path.join(os.path.dirname(__file__), 'users')
os.makedirs(ROOT_DIR, exist_ok=True)

# ----------------- Helpers -----------------
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_user_file(username):
    return os.path.join(ROOT_DIR, f"{username}.json")

def user_folder(username):
    folder = os.path.join(ROOT_DIR, username)
    os.makedirs(folder, exist_ok=True)
    return folder

def extract_token(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        m = re.search(r'BOT_TOKEN\s*=\s*[\'"](.+?)[\'"]', content)
        return m.group(1) if m else None
    except:
        return None

def get_bot_name(token):
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        if r.status_code==200:
            data = r.json()
            return data['result']['first_name']
    except:
        pass
    return "UnknownBot"

def get_bots(username):
    folder = user_folder(username)
    bots = []
    for f in os.listdir(folder):
        if f.endswith('_codefile.py'):
            bot_name = f.replace('_codefile.py','')
            pid_file = os.path.join(folder, bot_name+'_pid.txt')
            status = 'Running' if os.path.exists(pid_file) else 'Stopped'
            token = extract_token(os.path.join(folder, f))
            display = get_bot_name(token) if token else "UnknownBot"
            bots.append({'name':bot_name,'display':display,'status':status})
    return bots

# ----------------- Bot Start/Stop -----------------
def start_bot(username, bot_name):
    folder = user_folder(username)
    bot_file = os.path.join(folder, bot_name+'_codefile.py')
    pid_file = os.path.join(folder, bot_name+'_pid.txt')
    log_file = os.path.join(folder, bot_name+'_log.txt')

    if os.path.exists(bot_file):
        cmd = f"cd {folder} && nohup python3 {bot_name+'_codefile.py'} > {bot_name+'_log.txt'} 2>&1 & echo $!"
        pid = subprocess.getoutput(cmd)
        with open(pid_file,'w') as f:
            f.write(pid)

def stop_bot(username, bot_name):
    folder = user_folder(username)
    pid_file = os.path.join(folder, bot_name+'_pid.txt')
    if os.path.exists(pid_file):
        with open(pid_file,'r') as f:
            pid = f.read().strip()
        try:
            subprocess.run(['kill', pid])
        except:
            pass
        os.remove(pid_file)

# ----------------- Routes -----------------
@app.route('/', methods=['GET','POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    success = None

    if request.method=='POST' and 'upload' in request.form:
        f = request.files.get('codefile')
        pf = request.files.get('filephu')
        folder = user_folder(username)
        if f:
            f.save(os.path.join(folder, username+'_codefile.py'))
        if pf:
            pf.save(os.path.join(folder, pf.filename))
        success = "Upload thành công"

    bots = get_bots(username)
    return render_template_string(INDEX_HTML, username=username, bots=bots, success=success)

@app.route('/bot/<bot_name>/<action>')
def bot_action(bot_name, action):
    if 'user' not in session:
        return redirect(url_for('login'))
    username = session['user']
    if action=='start':
        start_bot(username, bot_name)
    elif action=='stop':
        stop_bot(username, bot_name)
    return redirect(url_for('index'))

# ----------------- Login/Register -----------------
@app.route('/login', methods=['GET','POST'])
def login():
    error_msg = None
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error_msg = "Vui lòng nhập đầy đủ thông tin"
        else:
            user_file = get_user_file(username)
            if os.path.exists(user_file):
                data = json.load(open(user_file))
                if hash_pass(password)==data['pass']:
                    session['user']=username
                    return redirect(url_for('index'))
            error_msg = "Đăng nhập thất bại"
    return render_template_string(LOGIN_HTML, error_msg=error_msg)

@app.route('/register', methods=['GET','POST'])
def register():
    error_msg = None
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error_msg = "Vui lòng nhập đầy đủ thông tin"
        else:
            user_file = get_user_file(username)
            if os.path.exists(user_file):
                error_msg = "Tài khoản đã tồn tại"
            else:
                json.dump({'pass':hash_pass(password)}, open(user_file,'w'))
                os.makedirs(user_folder(username), exist_ok=True)
                session['user'] = username
                return redirect(url_for('index'))
    return render_template_string(REGISTER_HTML, error_msg=error_msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- HTML -----------------
LOGIN_HTML = '''...'''       # Giữ nguyên mobile-friendly login
REGISTER_HTML = '''...'''    # Giữ nguyên mobile-friendly register
INDEX_HTML = '''...'''       # Giữ nguyên dashboard mobile-friendly

# ----------------- Run -----------------
if __name__=='__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
