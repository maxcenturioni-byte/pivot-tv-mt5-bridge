from flask import Flask, request, jsonify
from datetime import datetime, timezone
import os
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
    return jsonify({
        "status": "online",
        "service": "TradingView to MT5 Bridge"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    global latest_signal

    data = request.get_json(silent=True)

    if data is None:
        raw_text = request.get_data(as_text=True).strip()
        data = {"raw": raw_text}

    action = str(
        data.get("action")
        or data.get("order_action")
        or data.get("side")
        or ""
    ).strip().upper()

    symbol = str(
        data.get("symbol")
        or data.get("ticker")
        or ""
    ).strip().upper()

    price = data.get("price", None)

    # Supporto anche messaggi semplici tipo:
    # PIVOT|BUY|XAUUSD
    raw = str(data.get("raw", "")).strip()

    if raw:
        parts = [p.strip() for p in raw.split("|")]

        if len(parts) >= 2 and not action:
            action = parts[1].upper()

        if len(parts) >= 3 and not symbol:
            symbol = parts[2].upper()

    if action in ("LONG", "BUY", "1"):
        action = "BUY"
    elif action in ("SHORT", "SELL", "-1"):
        action = "SELL"
    else:
        return jsonify({
            "ok": False,
            "error": "Invalid action",
            "received": data
        }), 400

    with lock:
        new_id = latest_signal["id"] + 1

        latest_signal = {
            "id": new_id,
            "action": action,
            "symbol": symbol,
            "price": price,
            "time": datetime.now(timezone.utc).isoformat(),
            "raw": raw
        }

    return jsonify({
        "ok": True,
        "signal": latest_signal
    })

@app.route("/signal", methods=["GET"])
def signal():
    with lock:
        return jsonify(latest_signal)

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port) 
