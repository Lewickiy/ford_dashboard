import atexit
import os
import signal
import sys
import threading

from flask import Flask, jsonify, render_template
from werkzeug.serving import make_server

from collector import TelemetryCollector, TelemetryStorage
from obd_reader import ObdReader
from vehicle_processors import enrich_state

app = Flask(__name__)
shutdown_lock = threading.Lock()
shutdown_complete = False
http_server = None

obd = ObdReader()

obd.start()

storage = TelemetryStorage(os.getenv("TELEMETRY_DB_PATH", "data/telemetry.sqlite3"))
collector = TelemetryCollector(
    obd.get_state,
    storage=storage,
    save_interval=float(os.getenv("TELEMETRY_SAVE_INTERVAL", "1")),
    batch_size=int(os.getenv("TELEMETRY_BATCH_SIZE", "10")),
)
collector.start()


def shutdown_services():
    global shutdown_complete
    with shutdown_lock:
        if shutdown_complete:
            return
        print("[APP] Shutting down services...")
        collector_stopped = collector.stop(timeout=15.0)
        obd_stopped = obd.stop(timeout=10.0)
        if not collector_stopped:
            print("[APP] Telemetry collector did not stop before timeout")
        if not obd_stopped:
            print("[APP] OBD reader did not stop before timeout")
        shutdown_complete = True
        print("[APP] Shutdown complete")


def handle_signal(signum, _frame):
    print(f"[APP] Received signal {signum}")
    shutdown_services()
    sys.exit(0)


atexit.register(shutdown_services)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/data")
def data():
    state = enrich_state(obd.get_state())
    return jsonify(state)


if __name__ == "__main__":
    http_server = make_server("127.0.0.1", 5000, app, threaded=True)
    try:
        http_server.serve_forever()
    finally:
        shutdown_services()
