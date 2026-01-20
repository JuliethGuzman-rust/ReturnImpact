/* =====================================================================
   dashboard.js
   Purpose: Mini‑charts + count‑up animations for dashboard summary cards.
   Academic References:
     - Chart.js documentation: https://www.chartjs.org/docs/latest/
     - requestAnimationFrame: https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame
   ===================================================================== */



/* ------------------------------------------------------------
   COUNT-UP ANIMATION
------------------------------------------------------------- */
document.querySelectorAll(".countup").forEach(el => {
    const target = parseFloat(el.dataset.target);
    let current = 0;
    const duration = 1200;
    const step = target / (duration / 16);

    function update() {
        current += step;
        if (current >= target) {
            el.textContent = target;
        } else {
            el.textContent = current.toFixed(1);
            requestAnimationFrame(update);
        }
    }
    requestAnimationFrame(update);
});


/* ------------------------------------------------------------
   PREMIUM DUOTONE GRADIENTS
------------------------------------------------------------- */
function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 80);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}


/* ------------------------------------------------------------
   MINI CHARTS — Premium Sparkline Style
------------------------------------------------------------- */
const miniReturns = document.getElementById("miniReturnsChart").getContext("2d");
const miniCO2 = document.getElementById("miniCO2Chart").getContext("2d");
const miniCost = document.getElementById("miniCostChart").getContext("2d");


/* ------------------------------------------------------------
   RETURNS — LINE SPARKLINE
------------------------------------------------------------- */
new Chart(miniReturns, {
    type: "line",
    data: {
        labels: ["", "", "", "", ""],
        datasets: [{
            data: [2, 4, 3, 6, 5],
            borderColor: "rgba(104,125,49,1)",        // olive-green
            backgroundColor: createGradient(
                miniReturns,
                "rgba(104,125,49,0.35)",
                "rgba(104,125,49,0.05)"
            ),
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointRadius: 0
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { x: { display: false }, y: { display: false } },
        elements: { line: { borderCapStyle: "round" } }
    }
});


/* ------------------------------------------------------------
   CO₂ — BAR SPARKLINE
------------------------------------------------------------- */
new Chart(miniCO2, {
    type: "bar",
    data: {
        labels: ["", "", "", "", ""],
        datasets: [{
            data: [1, 3, 2, 4, 3],
            backgroundColor: createGradient(
                miniCO2,
                "rgba(64,103,104,0.8)",   // teal-dark
                "rgba(64,103,104,0.2)"
            ),
            borderColor: "rgba(64,103,104,1)",
            borderWidth: 2,
            borderRadius: 8
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { x: { display: false }, y: { display: false } }
    }
});


/* ------------------------------------------------------------
   COST — LINE SPARKLINE
------------------------------------------------------------- */
new Chart(miniCost, {
    type: "line",
    data: {
        labels: ["", "", "", "", ""],
        datasets: [{
            data: [10, 12, 9, 14, 13],
            borderColor: "rgba(111,169,187,1)",       // teal-light
            backgroundColor: createGradient(
                miniCost,
                "rgba(111,169,187,0.35)",
                "rgba(111,169,187,0.05)"
            ),
            borderWidth: 3,
            tension: 0.35,
            fill: true,
            pointRadius: 0
        }]
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { x: { display: false }, y: { display: false } },
        elements: { line: { borderCapStyle: "round" } }
    }
});
