"""Manual gear estimation for Ford Focus Mk2 style 5-speed layouts."""

# Approximate rpm-per-km/h bands for a Focus 2 1.4 petrol manual gearbox.
GEAR_BANDS = (
    ("5", 0, 34),
    ("4", 34, 48),
    ("3", 48, 72),
    ("2", 72, 112),
    ("1", 112, 999),
)


def estimate_gear(speed, rpm, throttle=0, load=0, intake_pressure=0, reverse_hint=False, clutch=False):
    """Estimate current gear from speed/rpm ratio and optional reverse hint.

    OBD-II does not expose a universal gear PID. Reverse is only reliable if a
    vehicle-specific reverse-light/CAN signal is available; otherwise we can
    only infer low-speed manoeuvring and mark it as uncertain.
    """
    if reverse_hint:
        return "R"

    if clutch:
        return "CL"

    if speed < 1:
        return "N" if rpm < 950 or throttle < 4 else "1"

    if speed < 5 and rpm > 1050 and throttle > 5:
        return "1"

    ratio = rpm / max(speed, 1)
    for gear, low, high in GEAR_BANDS:
        if low <= ratio < high:
            return gear
    return "?"
