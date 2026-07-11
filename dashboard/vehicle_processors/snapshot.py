"""Top-level processor that enriches raw OBD readings."""

from .alerts import build_alerts
from .clutch import clutch_state, is_clutch
from .driving_style import assess_driving_style
from .gear import estimate_gear
from .misfire import detect_misfires
from .shift import shift_advice


def enrich_state(raw):
    speed = raw.get("speed", 0.0)
    rpm = raw.get("rpm", 0.0)
    throttle = raw.get("throttle", 0.0)
    load = raw.get("load", 0.0)
    intake = raw.get("intake", 0.0)
    temp = raw.get("temp", 0.0)
    voltage = raw.get("voltage", 0.0)
    reverse_hint = bool(raw.get("reverse", False))

    clutch = is_clutch(speed, rpm, throttle, load)
    gear = estimate_gear(speed, rpm, throttle, load, intake, reverse_hint, clutch)
    misfire = detect_misfires(raw.get("dtc"), rpm, load, throttle)
    style = assess_driving_style(speed, rpm, throttle, load, temp, voltage)
    shift = shift_advice(rpm, throttle, load, gear)
    alerts = build_alerts(rpm, temp, load, misfire["cylinders"], clutch, gear)

    enriched = raw.copy()
    enriched.update(
        {
            "gear": gear,
            "clutch": clutch,
            "clutch_state": clutch_state(speed, rpm, throttle, load),
            "driving_style": style,
            "shift": shift,
            "misfire": misfire,
            "alerts": alerts,
        }
    )
    return enriched
