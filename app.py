from flask import Flask, request, jsonify
from datetime import datetime, timezone
import threading

app = Flask(__name__)

lock = threading.Lock()
latest_signal = {
    "id": 0,
    "action": "",
    "symbol": "",
    "price": None,
    "time": "",
    "raw": ""
}
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online"})

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_signal

    raw_text = request.get_data(as_text=True).strip()
    parts = [p.strip() for p in raw_text.split("|")]

    if len(parts) < 3 or parts[0] != "PIVOT":
        return jsonify({"ok": False, "error": "bad format", "received": raw_text}), 400

    action = parts[1].upper()
    symbol = parts[3].upper() if len(parts) > 3 else ""
    price = parts[4] if len(parts) > 4 else ""

    with lock:
        latest_signal = {
            "id": latest_signal["id"] + 1,
            "action": action,
            "symbol": symbol,
            "price": price,
            "time": datetime.now(timezone.utc).isoformat(),
            "raw": raw_text
        }

    return jsonify({"ok": True, "signal": latest_signal})

@app.route("/signal/<secret>", methods=["GET"])
def signal(Secret):
    with lock:
        return jsonify(latest_signal)
   
