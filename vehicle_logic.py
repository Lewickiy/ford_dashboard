# vehicle_logic.py


def is_clutch(speed, rpm, throttle, load):
    """
    Определение момента выжатого сцепления.

    Машина движется медленно,
    обороты есть,
    нагрузки почти нет.
    """

    if 0 < speed < 8:

        if rpm > 600 and throttle < 18 and load < 30:
            return True

    return False


def estimate_gear(
        speed,
        rpm,
        throttle,
        load,
        intake_pressure
):
    """
    Расчёт текущей передачи.

    Используем отношение:
        RPM / скорость

    Чем выше отношение,
    тем ниже передача.
    """

    # машина стоит
    if speed < 1:

        if rpm < 900:
            return "N"

        return "1"

    # старт с места
    if speed < 3 and rpm > 1200 and throttle > 5:
        return "1"

    ratio = rpm / max(speed, 1)

    if ratio < 22:
        return "5"

    elif ratio < 40:
        return "4"

    elif ratio < 65:
        return "3"

    elif ratio < 95:
        return "2"

    else:
        return "1"
