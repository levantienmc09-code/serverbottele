from flask import Flask, request, render_template_string, redirect, session, url_for
import os, hashlib, subprocess, json, re
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.join(ROOT_DIR, 'users')
os.makedirs(USER_DIR, exist_ok=True)

# ----------------- Helpers -----------------
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def get_user_file(username):
    return os.path.join(USER_DIR, f"{username}.json")

def user_folder(username):
    folder = os.path.join(USER_DIR, username)
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
    return render_template_string('''
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tele Bot Manager</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {background: linear-gradient(135deg, #667eea, #764ba2); min-height:100vh;}
.status-running {color: green; font-weight: bold;}
.status-stopped {color: red; font-weight: bold;}
.card {border-radius:15px; margin-top:20px;}
.table-responsive {overflow-x:auto;}
.btn {border-radius:50px;}
</style>
</head>
<body>
<div class="container">
    <nav class="navbar navbar-dark bg-primary rounded mt-3">
        <div class="container-fluid d-flex justify-content-between">
            <span class="navbar-brand mb-0 h1">Tele Bot Manager</span>
            <div>
                <span class="text-white me-3">{{username}}</span>
                <a class="btn btn-outline-light btn-sm" href="{{url_for('logout')}}">Đăng xuất</a>
            </div>
        </div>
    </nav>

    <div class="card">
        <div class="card-header bg-success text-white">Upload Bot Telegram</div>
        <div class="card-body">
            <form method="post" enctype="multipart/form-data">
                <div class="mb-2">
                    <input type="file" name="codefile" class="form-control" required>
                </div>
                <div class="mb-2">
                    <input type="file" name="filephu" class="form-control">
                </div>
                <button type="submit" name="upload" class="btn btn-primary w-100">Upload</button>
            </form>
            {% if success %}<div class="alert alert-success mt-2">{{success}}</div>{% endif %}
        </div>
    </div>

    <div class="card">
        <div class="card-header bg-info text-white">Danh sách Bot</div>
        <div class="card-body table-responsive">
            <table class="table table-hover table-bordered">
                <thead class="table-light">
                    <tr>
                        <th>Bot Name</th>
                        <th>Tên Bot Telegram</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                {% for bot in bots %}
                    <tr>
                        <td>{{bot.name}}</td>
                        <td>{{bot.display}}</td>
                        <td class="{{ 'status-running' if bot.status=='Running' else 'status-stopped' }}">{{bot.status}}</td>
                        <td>
                            {% if bot.status=='Running' %}
                            <a href="{{url_for('bot_action', bot_name=bot.name, action='stop')}}" class="btn btn-sm btn-danger w-100">Stop</a>
                            {% else %}
                            <a href="{{url_for('bot_action', bot_name=bot.name, action='start')}}" class="btn btn-sm btn-success w-100">Start</a>
                            {% endif %}
                        </td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
</body>
</html>
''', username=username, bots=bots, success=success)

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

@app.route('/login', methods=['GET','POST'])
def login():
    error_msg = None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user_file = get_user_file(username)
        if os.path.exists(user_file):
            data = json.load(open(user_file))
            if hash_pass(password)==data['pass']:
                session['user']=username
                return redirect(url_for('index'))
        error_msg = "Đăng nhập thất bại"

    return render_template_string('''
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Đăng Nhập</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {background: linear-gradient(135deg, #667eea, #764ba2); min-height:100vh; display:flex; justify-content:center; align-items:center;}
.card {border-radius:15px; padding:20px; width:100%; max-width:400px; box-shadow:0 8px 20px rgba(0,0,0,0.3);}
.btn {border-radius:50px;}
</style>
</head>
<body>
<div class="card text-center">
    <h2 class="mb-3 text-white">Đăng Nhập</h2>
    {% if error_msg %}
        <div class="alert alert-danger">{{error_msg}}</div>
    {% endif %}
    <form method="post">
        <div class="mb-3 text-start">
            <input type="text" name="username" class="form-control" placeholder="Tài khoản" required>
        </div>
        <div class="mb-3 text-start">
            <input type="password" name="password" class="form-control" placeholder="Mật khẩu" required>
        </div>
        <button type="submit" class="btn btn-primary w-100 mb-2">Đăng Nhập</button>
    </form>
    <p class="text-white">Chưa có tài khoản? <a href="/register" class="text-warning">Đăng Kí</a></p>
</div>
</body>
</html>
''', error_msg=error_msg)

@app.route('/register', methods=['GET','POST'])
def register():
    error_msg = None
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        user_file = get_user_file(username)
        if os.path.exists(user_file):
            error_msg = "Tài khoản đã tồn tại"
        else:
            json.dump({'pass':hash_pass(password)}, open(user_file,'w'))
            os.makedirs(user_folder(username), exist_ok=True)
            session['user'] = username
            return redirect(url_for('index'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Đăng Kí</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {background: linear-gradient(135deg, #ff758c, #ff7eb3); min-height:100vh; display:flex; justify-content:center; align-items:center;}
.card {border-radius:15px; padding:20px; width:100%; max-width:400px; box-shadow:0 8px 20px rgba(0,0,0,0.3);}
.btn {border-radius:50px;}
</style>
</head>
<body>
<div class="card text-center">
    <h2 class="mb-3 text-white">Đăng Kí</h2>
    {% if error_msg %}
        <div class="alert alert-danger">{{error_msg}}</div>
    {% endif %}
    <form method="post">
        <div class="mb-3 text-start">
            <input type="text" name="username" class="form-control" placeholder="Tài khoản" required>
        </div>
        <div class="mb-3 text-start">
            <input type="password" name="password" class="form-control" placeholder="Mật khẩu" required>
        </div>
        <button type="submit" class="btn btn-success w-100 mb-2">Đăng Kí</button>
    </form>
    <p class="text-white">Đã có tài khoản? <a href="/login" class="text-warning">Đăng Nhập</a></p>
</div>
</body>
</html>
''', error_msg=error_msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ----------------- Run -----------------
if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
