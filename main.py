from flask import Flask, render_template, request, redirect, url_for
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, ChallengeRequired, FeedbackRequired,
    ClientError, ClientForbiddenError, PleaseWaitFewMinutes
)
import threading
import time
import random
import os
import traceback

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# Global state
status = {"running": False, "sent": 0, "threads": 0, "logs": [], "text": "Ready"}
cfg = {
    "mode": "session",
    "username": "", "password": "",
    "sessionid1": "", "sessionid2": "",
    "thread_id": "", "messages": "",
    "delay": 60,          # safer default
    "cycle": 15,
    "break": 300,
}
clients = []
workers = []

# 2025-2026 looking devices
DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {msg}")
    if len(status["logs"]) > 800:
        status["logs"] = status["logs"][-800:]

def send_message(client, thread_id, message):
    for attempt in range(3):
        try:
            client.direct_send(message, thread_ids=[thread_id])
            return True
        except Exception as e:
            err = str(e).lower()
            if "feedback_required" in err or "challenge_required" in err:
                log("Challenge/Feedback detected → account likely blocked")
                return False
            log(f"Send attempt {attempt+1} failed: {str(e)[:120]}")
            time.sleep(random.uniform(8, 18))
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
                log(f"Sent #{status['sent']} → {msg[:45]}{'...' if len(msg)>45 else ''}")
            
            if local_sent % cfg["cycle"] == 0 and local_sent > 0:
                log(f"Cycle break → sleeping {cfg['break']}s")
                time.sleep(cfg["break"])
            
            time.sleep(max(30, cfg["delay"] + random.uniform(-6, 10)))  # safer min delay
        except Exception as e:
            log(f"Bomber error: {str(e)[:100]}")
            time.sleep(30)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        try:
            log("POST received - starting new session")

            status["running"] = False
            time.sleep(1.5)
            status["logs"].clear()
            status["sent"] = 0
            clients.clear()
            workers.clear()

            # Safe form reading
            form = request.form
            cfg["mode"] = form.get("mode", "session")
            cfg["username"] = form.get("username", "").strip()
            cfg["password"] = form.get("password", "").strip()
            cfg["sessionid1"] = form.get("sessionid1", "").strip()
            cfg["sessionid2"] = form.get("sessionid2", "").strip()
            cfg["thread_id"] = form.get("thread_id", "").strip()
            cfg["messages"] = form.get("messages", "").strip()

            try:
                cfg["delay"] = float(form.get("delay", 60))
                if cfg["delay"] < 30: cfg["delay"] = 60
            except:
                cfg["delay"] = 60
                log("Invalid delay → using 60s")

            try:
                cfg["cycle"] = int(form.get("cycle", 15))
                if cfg["cycle"] < 5: cfg["cycle"] = 15
            except:
                cfg["cycle"] = 15
                log("Invalid cycle → using 15")

            try:
                cfg["break"] = int(form.get("break", 300))
                if cfg["break"] < 60: cfg["break"] = 300
            except:
                cfg["break"] = 300
                log("Invalid break → using 300s")

            log(f"Config → mode:{cfg['mode']} delay:{cfg['delay']}s cycle:{cfg['cycle']} break:{cfg['break']}s")

            # Messages
            raw_msgs = cfg["messages"]
            msgs = [m.strip() for m in raw_msgs.splitlines() if m.strip()]
            if not msgs:
                msgs = ["test"]
                log("No messages → fallback 'test'")

            # Thread ID
            try:
                tid = int(cfg["thread_id"])
                if tid <= 0:
                    raise ValueError("Thread ID must be positive")
                log(f"Target thread ID: {tid}")
            except Exception as e:
                log(f"Invalid thread_id: {str(e)}")
                status["text"] = "Invalid Thread ID (must be positive number)"
                return render_template('index.html', **status, cfg=cfg, error=str(e))

            # Accounts
            accounts = []
            if cfg["mode"] == "session":
                if cfg["sessionid1"]: accounts.append(cfg["sessionid1"])
                if cfg["sessionid2"]: accounts.append(cfg["sessionid2"])
            else:
                if cfg["username"] and cfg["password"]:
                    accounts.append(("username", cfg["username"], cfg["password"]))
                else:
                    accounts.append(None)

            status["running"] = True
            status["text"] = "STARTING..."
            log("─── INITIALIZING ACCOUNTS ───")

            for idx, acc in enumerate(accounts[:2], 1):
                if acc is None:
                    log(f"Account {idx} → skipped (no credentials)")
                    continue

                cl = Client()
                device = random.choice(DEVICES)
                cl.set_device(device)
                cl.set_user_agent(
                    f"Instagram {device['app_version']} Android "
                    f"(34/15.0.0; 480dpi; 1080x2340; {device['phone_manufacturer']}; "
                    f"{device['phone_model']}; raven; raven; en_US)"
                )
                cl.delay_range = [8, 25]

                try:
                    if cfg["mode"] == "session":
                        cl.login_by_sessionid(acc)
                        user = cl.account_info()
                        username = user.username if user else "?"
                        log(f"Account {idx} → SUCCESS (session) → @{username}")
                    else:
                        # username/pass mode
                        uname, pwd = acc[1], acc[2]
                        cl.login(uname, pwd)
                        log(f"Account {idx} → SUCCESS (login) → @{uname}")
                    clients.append(cl)
                except (LoginRequired, ClientForbiddenError):
                    log(f"Account {idx} → LoginRequired / Forbidden → session likely dead")
                except ChallengeRequired:
                    log(f"Account {idx} → ChallengeRequired → needs verification")
                except FeedbackRequired:
                    log(f"Account {idx} → FeedbackRequired → action blocked")
                except PleaseWaitFewMinutes:
                    log(f"Account {idx} → PleaseWaitFewMinutes → rate limited")
                except Exception as e:
                    log(f"Account {idx} → FAILED: {type(e).__name__} → {str(e)[:140]}")

            # Start threads
            if clients:
                status["text"] = f"BOMBING ({len(clients)} accounts)"
                log(f"Launching {len(clients)} bomber threads")
                for cl in clients:
                    t = threading.Thread(target=bomber, args=(cl, tid, msgs), daemon=True)
                    t.start()
                    workers.append(t)
                status["threads"] = len(clients)
            else:
                status["running"] = False
                status["text"] = "ALL LOGINS FAILED"
                log("!!! NO SUCCESSFUL LOGINS - check session IDs !!!")

        except Exception as e:
            tb = traceback.format_exc()
            log(f"CRITICAL ERROR during start:\n{tb[:500]}")
            status["text"] = "Server crashed - see logs"
            status["running"] = False
            error = str(e)

    return render_template('index.html', **status, cfg=cfg, error=error)

@app.route('/stop')
def stop():
    status["running"] = False
    log("→ STOPPED BY USER ←")
    status["text"] = "STOPPED"
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
