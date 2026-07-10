from flask import Flask, jsonify, render_template

from obd_reader import ObdReader
from vehicle_processors import enrich_state

app = Flask(__name__)

obd = ObdReader()

obd.start()


@app.route("/")
def index():
    return render_template(
        "index.html"
    )


@app.route("/data")
def data():
    state = enrich_state(obd.get_state())

    return jsonify(state)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False
    )
