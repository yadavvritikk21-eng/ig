from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# Global
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
cfg = {
    "mode": "session",
    "sessionid1": "", "sessionid2": "",
    "thread_id": "", "messages": "", "delay": 12,
    "cycle": 35, "break": 40, "threads": 2  # Fixed to 2 threads for 2 sessions
}

clients = []
workers = []

# Super undetected devices (2025 latest – no block)
DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {msg}")
    if len(status["logs"]) > 600:
        status["logs"] = status["logs"][-600:]

def send_message(client, thread_id, message):
    for _ in range(3):  # Retry 3 times for send
        try:
            client.direct_send(message, thread_ids=[thread_id])
            return True
        except Exception as e:
            if "feedback_required" in str(e) or "challenge_required" in str(e):
                log("Challenge/Feedback detected – skipping message")
                return False
            time.sleep(random.uniform(5, 10))
    log("Message send failed after 3 retries")
    return False

def bomber(cl, tid, msgs, session_num):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            if send_message(cl, tid, msg):
                local_sent += 1
                status["sent"] += 1
                log(f"Session{session_num} → Sent #{status['sent']} → {msg[:50]}")
            
            if local_sent % cfg["cycle"] == 0:
                log(f"Session{session_num} → Break {cfg['break']}s after {cfg['cycle']} msgs")
                time.sleep(cfg["break"])
            
            time.sleep(cfg["delay"] + random.uniform(-2, 3))
        except:
            time.sleep(20)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        status["running"] = False
        time.sleep(2)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        cfg.update({
            "mode": "session",  # Force session mode
            "sessionid1": request.form.get('sessionid1', '').strip(),
            "sessionid2": request.form.get('sessionid2', '').strip(),
            "thread_id": request.form['thread_id'],
            "messages": request.form['messages'],
            "delay": float(request.form.get('delay', 12)),
            "cycle": int(request.form.get('cycle', 35)),
            "break": int(request.form.get('break', 40)),
            "threads": 2  # Always 2 for dual sessions
        })

        # Split messages by newline
        msgs = [m.strip() for m in cfg["messages"].split('\n') if m.strip()]
        if not msgs:
            msgs = [cfg["messages"]]
        
        tid = int(cfg["thread_id"])
        session_ids = [cfg["sessionid1"], cfg["sessionid2"]]

        status["running"] = True
        status["text"] = "BOMBING ACTIVE"
        log("DUAL SESSION SPAMMER STARTED – HAWK SUJAL PRO")

        for i in range(2):  # Exactly 2 sessions
            if not session_ids[i]:
                log(f"Session {i+1} skipped → No session ID")
                continue
                
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.set_user_agent(f"Instagram {device['app_version']} Android (34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; {device['phone_model']}; raven; raven; en_US)")
            cl.delay_range = [8, 25]

            try:
                cl.login_by_sessionid(session_ids[i])
                log(f"Session {i+1} → Login SUCCESS")
                clients.append(cl)
                t = threading.Thread(target=bomber, args=(cl, tid, msgs, i+1), daemon=True)
                t.start()
                workers.append(t)

            except Exception as e:
                log(f"Session {i+1} Failed → {str(e)[:90]}")

        status["threads"] = len(clients)
        if not clients:
            status["text"] = "ALL LOGIN FAILED"
            status["running"] = False

    return render_template('index.html', **status, cfg=cfg)

@app.route('/stop')
def stop():
    status["running"] = False
    log("SPAMMER STOPPED BY USER")
    status["text"] = "STOPPED"
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
