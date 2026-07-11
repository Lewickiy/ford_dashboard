"""Misfire detection helpers.

Generic OBD-II can read stored DTCs. Cylinder-specific misfire counters are
manufacturer-specific, so without Ford enhanced PIDs we mark cylinders as
suspect only when P0301-P0304 DTCs are present and use load/rpm drops as a
common-warning flag.
"""

MISFIRE_CODES = {"P0301": "cyl1", "P0302": "cyl2", "P0303": "cyl3", "P0304": "cyl4"}


def _normalise_codes(dtc):
    if not dtc:
        return []
    codes = []
    for item in dtc:
        if isinstance(item, (list, tuple)) and item:
            codes.append(str(item[0]))
        else:
            codes.append(str(item))
    return codes


def detect_misfires(dtc, rpm, load, throttle):
    status = {"cyl1": "ok", "cyl2": "ok", "cyl3": "ok", "cyl4": "ok"}
    codes = _normalise_codes(dtc)
    for code in codes:
        cyl = MISFIRE_CODES.get(code)
        if cyl:
            status[cyl] = "suspect"
    rough_running = rpm > 900 and throttle > 15 and load < 18
    return {"cylinders": status, "codes": codes, "rough_running": rough_running}
