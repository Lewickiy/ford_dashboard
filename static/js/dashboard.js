const speedCanvas = document.getElementById("speed");
const rpmCanvas = document.getElementById("rpm");
const tempCanvas = document.getElementById("temp");

const sctx = speedCanvas.getContext("2d");
const rctx = rpmCanvas.getContext("2d");
const tctx = tempCanvas.getContext("2d");

const CENTER = 150;
const RADIUS = 110;

// текущее состояние стрелок (для инерции)
let state = {
    speed: 0,
    rpm: 0,
    temp: 0
};

// перевод в угол
function valueToAngle(value, max) {
    const startAngle = Math.PI * 0.75;
    const endAngle = Math.PI * 2.25;
    const ratio = Math.min(value / max, 1);
    return startAngle + ratio * (endAngle - startAngle);
}

// рисуем прибор
function drawNeedleGauge(ctx, value, max, label, unit) {
    ctx.clearRect(0, 0, 300, 300);

    const startAngle = Math.PI * 0.75;
    const endAngle = Math.PI * 2.25;

    // фон
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, RADIUS, startAngle, endAngle);
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 18;
    ctx.stroke();

    const angle = valueToAngle(value, max);

    // дуга прогресса
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, RADIUS, startAngle, angle);
    ctx.strokeStyle = "#00ff99";
    ctx.lineWidth = 18;
    ctx.stroke();

    // стрелка
    const needleLength = 95;
    const x = CENTER + Math.cos(angle) * needleLength;
    const y = CENTER + Math.sin(angle) * needleLength;

    ctx.beginPath();
    ctx.moveTo(CENTER, CENTER);
    ctx.lineTo(x, y);
    ctx.strokeStyle = "white";
    ctx.lineWidth = 3;
    ctx.stroke();

    // центр
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, 6, 0, Math.PI * 2);
    ctx.fillStyle = "white";
    ctx.fill();

    // текст
    ctx.fillStyle = "white";
    ctx.font = "bold 26px Arial";
    ctx.textAlign = "center";
    ctx.fillText(label, CENTER, CENTER - 10);

    ctx.font = "20px Arial";
    ctx.fillText(Math.round(value) + " " + unit, CENTER, CENTER + 30);
}

// плавное приближение (инерция стрелок)
function lerp(a, b, t) {
    return a + (b - a) * t;
}

// основной цикл
async function update() {
    try {
        const res = await fetch("/data");
        const data = await res.json();

        // обновляем цель
        state.speed = data.speed || 0;
        state.rpm = data.rpm || 0;
        state.temp = data.temp || 0;

    } catch (e) {
        // если связь пропала — плавно падаем в ноль
        state.speed *= 0.90;
        state.rpm *= 0.90;
        state.temp *= 0.95;
    }

    // рендер с инерцией
    drawNeedleGauge(sctx, state.speed, 200, "SPEED", "km/h");
    drawNeedleGauge(rctx, state.rpm, 6000, "RPM", "rpm");
    drawNeedleGauge(tctx, state.temp, 120, "TEMP", "°C");

    // текст
    document.getElementById("speedText").innerText = Math.round(state.speed) + " km/h";
    document.getElementById("rpmText").innerText = Math.round(state.rpm) + " rpm";
    document.getElementById("gearText").innerText = data.gear;
    document.getElementById("tempText").innerText = Math.round(state.temp) + " °C";
}

// 5 раз в секунду
setInterval(update, 200);
update();