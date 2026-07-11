"""Clutch slip / pressed-pedal heuristics."""


def is_clutch(speed, rpm, throttle, load):
    """Return True when rpm exists but road speed/load are very low."""
    return 0 < speed < 10 and rpm > 700 and throttle < 22 and load < 35


def clutch_state(speed, rpm, throttle, load):
    if is_clutch(speed, rpm, throttle, load):
        return "pressed"
    if speed < 3 and 900 < rpm < 1600 and throttle < 12:
        return "creeping"
    return "engaged"
