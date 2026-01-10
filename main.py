from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

# ---------------- GLOBAL STATE ----------------
status = {
    "running": False,
    "sent": 0,
    "threads": 0,
    "logs": [],
    "text": "Ready"
}

cfg = {
    "mode": "username",
    "username": "",
    "password": "",
    "sessionid": "",
    "thread_id": "",
    "messages": "",
    "delay": 12,
    "cycle": 35,
    "break": 40,
    "threads": 1
}

clients = []
workers = []

# ---------------- DEVICES ----------------
DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
    {"phone_manufacturer": "Xiaomi", "phone_model": "23127PN0CC", "android_version": 15, "android_release": "15.0.0", "app_version": "325.0.0.42.111"},
]

# ---------------- UTIL ----------------
def log(msg):
    ts = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{ts}] {msg}")
    status["logs"] = status["logs"][-600:]

# ---------------- MESSAGE SEND ----------------
def send_message(client, thread_id, message):
    try:
        client.direct_send(message, thread_ids=[thread_id])
        return True
    except Exception as e:
        log(f"Send failed: {str(e)[:80]}")
        return False

# ---------------- WORKER ----------------
def bomber(client, tid, message):
    sent_local = 0
    while status["running"]:
        if send_message(client, tid, message):
            sent_local += 1
            status["sent"] += 1
            log(f"Sent #{status['sent']}")

        if sent_local % cfg["cycle"] == 0:
            log(f"Break {cfg['break']}s")
            time.sleep(cfg["break"])

        time.sleep(cfg["delay"])

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # STOP previous run safely
        status["running"] = False
        time.sleep(1)

        status["logs"].clear()
        status["sent"] = 0
        clients.clear()
        workers.clear()

        # SAFE PARSING (NO CRASH)
        try:
            threads_val = int(request.form.get("threads", "1"))
        except:
            threads_val = 1

        try:
            tid = int(request.form["thread_id"])
        except:
            return "Invalid Thread ID", 400

        cfg.update({
            "mode": request.form.get("mode", "username"),
            "username": request.form.get("username", ""),
            "password": request.form.get("password", ""),
            "sessionid": request.form.get("sessionid", "").strip(),
            "thread_id": tid,
            "messages": request.form.get("messages", ""),
            "delay": float(request.form.get("delay", 12)),
            "cycle": int(request.form.get("cycle", 35)),
            "break": int(request.form.get("break", 40)),
            "threads": threads_val
        })

        if not cfg["messages"].strip():
            return "Message cannot be empty", 400

        status["running"] = True
        status["text"] = "RUNNING"
        log("Panel started")

        for i in range(cfg["threads"]):
            cl = Client()
            device = random.choice(DEVICES)
            cl.set_device(device)
            cl.delay_range = [8, 25]

            try:
                if cfg["mode"] == "session" and cfg["sessionid"]:
                    cl.login_by_sessionid(cfg["sessionid"])
                    log(f"Thread {i+1} session login OK")
                else:
                    cl.login(cfg["username"], cfg["password"])
                    log(f"Thread {i+1} user login OK")

                t = threading.Thread(
                    target=bomber,
                    args=(cl, cfg["thread_id"], cfg["messages"]),
                    daemon=True
                )
                t.start()
                clients.append(cl)
                workers.append(t)

            except Exception as e:
                log(f"Thread {i+1} failed: {str(e)[:80]}")

        status["threads"] = len(workers)

    return render_template("index.html", **status, cfg=cfg)

@app.route("/stop")
def stop():
    status["running"] = False
    status["text"] = "STOPPED"
    log("Stopped by user")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
