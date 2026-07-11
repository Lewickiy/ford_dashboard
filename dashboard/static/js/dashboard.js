const gauges = {
    speed: document.getElementById("speed").getContext("2d"),
    rpm: document.getElementById("rpm").getContext("2d"),
    temp: document.getElementById("temp").getContext("2d")
};

let target = {speed: 0, rpm: 0, temp: 0, throttle: 0, load: 0, intake: 0, voltage: 0};
let display = {...target};
let lastData = {
    gear: "N",
    connected: false,
    shift: {state: "off", text: ""},
    alerts: ["Системы в норме"],
    misfire: {cylinders: {}}
};

function valueToAngle(value, max) {
    const startAngle = Math.PI * 0.76;
    const endAngle = Math.PI * 2.24;
    return startAngle + Math.min(Math.max(value / max, 0), 1) * (endAngle - startAngle);
}

function drawGauge(ctx, value, max, label, unit, redFrom = 0.82) {
    const canvas = ctx.canvas;
    const center = canvas.width / 2;
    const radius = canvas.width * 0.36;
    const startAngle = Math.PI * 0.76;
    const endAngle = Math.PI * 2.24;
    const angle = valueToAngle(value, max);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.shadowColor = "rgba(90, 180, 255, 0.22)";
    ctx.shadowBlur = 24;
    ctx.beginPath();
    ctx.arc(center, center, radius + 18, 0, Math.PI * 2);
    ctx.fillStyle = "#05070b";
    ctx.fill();
    ctx.restore();

    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.arc(center, center, radius, startAngle, endAngle);
    ctx.strokeStyle = "#26303b";
    ctx.lineWidth = 18;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(center, center, radius, startAngle, angle);
    ctx.strokeStyle = value / max > redFrom ? "#ff2f36" : "#d7efff";
    ctx.lineWidth = 12;
    ctx.stroke();

    for (let i = 0; i <= 10; i += 1) {
        const tickAngle = startAngle + (i / 10) * (endAngle - startAngle);
        const inner = radius - (i % 2 === 0 ? 18 : 10);
        const outer = radius + 4;
        ctx.beginPath();
        ctx.moveTo(center + Math.cos(tickAngle) * inner, center + Math.sin(tickAngle) * inner);
        ctx.lineTo(center + Math.cos(tickAngle) * outer, center + Math.sin(tickAngle) * outer);
        ctx.strokeStyle = i >= 8 ? "#ff4b4b" : "#e9f6ff";
        ctx.lineWidth = i % 2 === 0 ? 3 : 1.5;
        ctx.stroke();
    }

    const needleLength = radius - 8;
    ctx.beginPath();
    ctx.moveTo(center, center);
    ctx.lineTo(center + Math.cos(angle) * needleLength, center + Math.sin(angle) * needleLength);
    ctx.strokeStyle = "#f3f7fb";
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(center, center, 10, 0, Math.PI * 2);
    ctx.fillStyle = "#d51f27";
    ctx.fill();

    ctx.fillStyle = "#eef7ff";
    ctx.textAlign = "center";
    ctx.font = `700 ${canvas.width > 300 ? 28 : 22}px Arial`;
    ctx.fillText(label, center, center - 12);
    ctx.font = `${canvas.width > 300 ? 20 : 16}px Arial`;
    ctx.fillText(`${Math.round(value)} ${unit}`, center, center + 28);
}

function lerp(a, b, t) {
    return a + (b - a) * t;
}

function setText(id, text) {
    document.getElementById(id).innerText = text;
}

async function poll() {
    try {
        const res = await fetch("/data", {cache: "no-store"});
        lastData = await res.json();
        ["speed", "rpm", "temp", "throttle", "load", "intake", "voltage"].forEach((key) => {
            target[key] = Number(lastData[key] || 0);
        });
    } catch (e) {
        lastData.connected = false;
        Object.keys(target).forEach((key) => {
            target[key] *= 0.9;
        });
    }
}

function render() {
    Object.keys(display).forEach((key) => {
        display[key] = lerp(display[key], target[key], 0.18);
    });

    drawGauge(gauges.speed, display.speed, 220, "SPEED", "km/h");
    drawGauge(gauges.rpm, display.rpm, 6500, "RPM", "rpm", 0.68);
    drawGauge(gauges.temp, display.temp, 120, "TEMP", "°C", 0.84);

    setText("speedText", `${Math.round(display.speed)} km/h`);
    setText("rpmText", `${Math.round(display.rpm)} rpm`);
    setText("tempText", `${Math.round(display.temp)} °C`);
    setText("gearText", lastData.gear || "?");
    setText("clutchText", `Clutch: ${lastData.clutch_state || "—"}`);
    setText("throttleText", `${Math.round(display.throttle)}%`);
    setText("loadText", `${Math.round(display.load)}%`);
    setText("intakeText", `${Math.round(display.intake)} kPa`);
    setText("voltageText", `${display.voltage.toFixed(1)} V`);
    setText("styleText", lastData.driving_style || "—");
    setText("alertsText", (lastData.alerts || []).join(" • "));
    setText("dtcText", `DTC: ${(lastData.misfire?.codes || []).join(", ") || "—"}`);

    setText("vinText", lastData.vin || "—");

    const connection = document.getElementById("connectionIndicator");
    const status = lastData.connection_status || (lastData.connected ? "connected" : "disconnected");
    connection.className = `connection ${status}`;
    const statusLabels = {
        disconnected: "DISCONNECTED",
        connected: "CONNECTED",
        koeo: "KOEO",
        koer: "KOER"
    };
    setText("connectionText", statusLabels[status] || "DISCONNECTED");

    const shiftLight = document.getElementById("shiftLight");
    shiftLight.className = `shift-light ${lastData.shift?.state || "off"}`;

    const cylinders = lastData.misfire?.cylinders || {};
    ["cyl1", "cyl2", "cyl3", "cyl4"].forEach((id, index) => {
        const el = document.getElementById(id);
        const suspect = cylinders[id] === "suspect";
        el.className = `cyl ${suspect ? "fail" : "ok"}`;
        el.innerText = `Cyl ${index + 1} ${suspect ? "⚠" : "✔"}`;
    });

    requestAnimationFrame(render);
}

setInterval(poll, 250);
poll();
render();
