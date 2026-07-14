"""Driving style and vehicle load assessment."""


def assess_driving_style(speed, rpm, throttle, load, temp, voltage=0):
    score = 0
    if rpm > 3500:
        score += 2
    elif rpm > 2800:
        score += 1
    if throttle > 70:
        score += 2
    elif throttle > 45:
        score += 1
    if load > 80:
        score += 2
    elif load > 60:
        score += 1
    if temp > 105:
        score += 2
    if score >= 5 and voltage > 10:
        return "Агрессивная езда / высокая нагрузка"
    if score >= 3 and voltage > 10:
        return "Активная езда"
    if speed == 0 and rpm == 0 and voltage > 10:
        return "Двигатель заглушен"
    if speed == 0 and 600 < rpm < 1200 and voltage > 10:
        return "Двигатель работает на холостом ходу"
    if speed < 10 and rpm < 1800 and voltage > 10:
        return "Маневрирование / пробка"
    if voltage < 10:
        return "—"
    return "Спокойная езда"
