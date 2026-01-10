from flask import Flask, render_template, request, redirect
from instagrapi import Client
import threading
import time
import random
import os

app = Flask(__name__)
app.secret_key = "sujal_hawk_final_2025"

status = {
    "running": False,
    "sent": 0,
    "threads": 0,
    "logs": [],
    "text": "Ready"
}

cfg = {
    "mode": "session",
    "sessionid_1": "",
    "sessionid_2": "",
    "thread_id_1": "",
    "thread_id_2": "",
    "messages": "",
    "delay": 12,
    "cycle": 35,
    "break": 40
}

clients = []

DEVICES = [
    {"phone_manufacturer": "Google", "phone_model": "Pixel 8 Pro", "android_version": 15, "android_release": "15.0.0", "app_version": "323.0.0.46.109"},
    {"phone_manufacturer": "Samsung", "phone_model": "SM-S928B", "android_version": 15, "android_release": "15.0.0", "app_version": "324.0.0.41.110"},
    {"phone_manufacturer": "OnePlus", "phone_model": "PJZ110", "android_version": 15, "android_release": "15.0.0", "app_version": "322.0.0.40.108"},
]

def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    status["logs"].append(f"[{timestamp}] {msg}")
    if len(status["logs"]) > 600:
        status["logs"] = status["logs"][-600:]

def send_message(cl, tid, msg, tag):
    try:
        cl.direct_send(msg, thread_ids=[tid])
        status["sent"] += 1
        log(f"{tag} Sent #{status['sent']}")
        return True
    except Exception as e:
        log(f"{tag} Send failed")
        return False

def worker(tag, sessionid, thread_id, message):
    cl = Client()
    device = random.choice(DEVICES)
    cl.set_device(device)
    cl.set_user_agent(
        f"Instagram {device['app_version']} Android "
        f"(34/15.0.0; {device['phone_manufacturer']}; {device['phone_model']})"
    )

    try:
        cl.login_by_sessionid(sessionid)
        log(f"{tag} Login SUCCESS")
    except Exception:
        log(f"{tag} Login FAILED")
        return

    local_sent = 0
    while status["running"]:
        if send_message(cl, thread_id, message, tag):
            local_sent += 1

        if local_sent % cfg["cycle"] == 0:
            log(f"{tag} Break {cfg['break']}s")
            time.sleep(cfg["break"])

        time.sleep(cfg["delay"] + random.uniform(-2, 3))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        status["running"] = False
        time.sleep(2)
        status["logs"].clear()
        status["sent"] = 0
        clients.clear()

        cfg.update({
            "sessionid_1": request.form["sessionid_1"].strip(),
            "sessionid_2": request.form["sessionid_2"].strip(),
            "thread_id_1": int(request.form["thread_id_1"]),
            "thread_id_2": int(request.form["thread_id_2"]),
            "messages": request.form["messages"],
            "delay": float(request.form["delay"]),
            "cycle": int(request.form["cycle"]),
            "break": int(request.form["break"]),
        })

        status["running"] = True
        status["text"] = "RUNNING (2 ACCOUNTS)"

        t1 = threading.Thread(
            target=worker,
            args=("[ACC-1]", cfg["sessionid_1"], cfg["thread_id_1"], cfg["messages"]),
            daemon=True
        )
        t2 = threading.Thread(
            target=worker,
            args=("[ACC-2]", cfg["sessionid_2"], cfg["thread_id_2"], cfg["messages"]),
            daemon=True
        )

        t1.start()
        t2.start()
        status["threads"] = 2

    return render_template("index.html", **status, cfg=cfg)

@app.route("/stop")
def stop():
    status["running"] = False
    status["text"] = "STOPPED"
    log("STOPPED BY USER")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
