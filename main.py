from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# Global state
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
cfg = {
    "mode": "username",
    "username": "", "password": "", 
    "sessionid1": "", "sessionid2": "",
    "thread_id": "", "messages": "",
    "delay": 12,
    "cycle": 35, "break": 40,
    "threads": 2   # default changed to 2
}

clients = []
workers = []

# 2025-2026 relatively safe looking devices
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
    for _ in range(3):
        try:
            client.direct_send(message, thread_ids=[thread_id])
            return True
        except Exception as e:
            err = str(e)
            if "feedback_required" in err or "challenge_required" in err:
                log("Challenge/Feedback detected → skipping")
                return False
            time.sleep(random.uniform(5, 12))
    log("Failed to send after 3 attempts")
    return False

def bomber(cl, tid, msgs):
    local_sent = 0
    while status["running"]:
        try:
            msg = random.choice(msgs)
            if send_message(cl, tid, msg):
                local_sent += 1
                status["sent"] += 1
                log(f"Sent #{status['sent']} → {msg[:50]}{'...' if len(msg)>50 else ''}")
            
            if local_sent % cfg["cycle"] == 0 and local_sent > 0:
                log(f"Cycle break → sleeping {cfg['break']}s")
                time.sleep(cfg["break"])
            
            time.sleep(cfg["delay"] + random.uniform(-3, 4))
        except:
            time.sleep(25)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # First — stop everything
        status["running"] = False
        time.sleep(1.8)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        # Read form
        cfg.update({
            "mode": request.form.get('mode', 'username'),
            "username": request.form.get('username', ''),
            "password": request.form.get('password', ''),
            "sessionid1": request.form.get('sessionid1', '').strip(),
            "sessionid2": request.form.get('sessionid2', '').strip(),
            "thread_id": request.form['thread_id'].strip(),
            "messages": request.form['messages'],
            "delay": float(request.form.get('delay', 12)),
            "cycle": int(request.form.get('cycle', 35)),
            "break": int(request.form.get('break', 40)),
        })

        # Prepare messages (split by lines if many)
        raw_msgs = cfg["messages"].strip()
        msgs = [m.strip() for m in raw_msgs.split('\n') if m.strip()]
        if not msgs:
            msgs = ["test message"]

        try:
            tid = int(cfg["thread_id"])
        except:
            status["text"] = "Invalid Thread ID!"
            status["running"] = False
            return render_template('index.html', **status, cfg=cfg)

        # Decide how many accounts we will try
        accounts_to_use = []
        if cfg["mode"] == "session":
            if cfg["sessionid1"]:
                accounts_to_use.append(cfg["sessionid1"])
            if cfg["sessionid2"]:
                accounts_to_use.append(cfg["sessionid2"])
            max_threads = len(accounts_to_use)  # 1 or 2
        else:
            accounts_to_use = [None]  # placeholder for username/pass
            max_threads = 1  # username/pass mode — usually only 1

        status["running"] = True
        status["text"] = "STARTING..."
        log("─── SPAMMER INITIALIZING ───")

        for i, session_id in enumerate(accounts_to_use[:2]):  # max 2
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.set_user_agent(
                f"Instagram {device['app_version']} Android "
                f"(34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; "
                f"{device['phone_model']}; raven; raven; en_US)"
            )
            cl.delay_range = [9, 28]

            try:
                if cfg["mode"] == "session" and session_id:
                    cl.login_by_sessionid(session_id)
                    log(f"Account {i+1} → Session login SUCCESS")
                else:
                    cl.login(cfg["username"], cfg["password"])
                    log(f"Account {i+1} → Username/Password login SUCCESS")

                clients.append(cl)

            except Exception as e:
                log(f"Account {i+1} FAILED → {str(e)[:100]}")

        # Start bombing threads only for successful logins
        workers.clear()
        if clients:
            status["text"] = f"BOMBING — {len(clients)} account(s)"
            log(f"→ Starting {len(clients)} threads ←")
            for cl in clients:
                t = threading.Thread(target=bomber, args=(cl, tid, msgs), daemon=True)
                t.start()
                workers.append(t)
        else:
            status["text"] = "ALL LOGINS FAILED"
            status["running"] = False
            log("!!! NO WORKING ACCOUNTS !!!")

        status["threads"] = len(clients)

    return render_template('index.html', **status, cfg=cfg)


@app.route('/stop')
def stop():
    status["running"] = False
    log("→ SPAMMER STOPPED BY USER ←")
    status["text"] = "STOPPED"
    return redirect('/')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
