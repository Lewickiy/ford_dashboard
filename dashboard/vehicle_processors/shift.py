"""Shift-light recommendations."""


def shift_advice(rpm, throttle, load, gear):
    if gear in {"N", "R", "CL", "?"}:
        return {"state": "off", "text": ""}
    if rpm >= 4200 or (rpm >= 3600 and load > 75):
        return {"state": "red", "text": "SHIFT"}
    if rpm >= 2500 and throttle < 65:
        return {"state": "green", "text": "SHIFT"}
    return {"state": "off", "text": ""}
