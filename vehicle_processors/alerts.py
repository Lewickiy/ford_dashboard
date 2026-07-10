"""Human-readable warnings built from processed telemetry."""


def build_alerts(rpm, temp, load, misfires, clutch, gear):
    alerts = []
    if temp >= 110:
        alerts.append("Температура ОЖ критически высокая")
    elif temp >= 100:
        alerts.append("Температура ОЖ повышена")
    if rpm >= 4500:
        alerts.append("Высокие обороты двигателя")
    if load >= 85:
        alerts.append("Высокая нагрузка на двигатель")
    if clutch:
        alerts.append("Сцепление выжато/поджато")
    if gear == "?":
        alerts.append("Передача не определена")
    failed = [cyl for cyl, status in misfires.items() if status == "suspect"]
    if failed:
        alerts.append("Возможны пропуски зажигания: " + ", ".join(failed))
    return alerts or ["Системы в норме"]
