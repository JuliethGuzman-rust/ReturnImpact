/* =====================================================================
   analytics.js
   Purpose: Count-up animations, premium duotone Chart.js rendering,
            and dynamic CO₂ visualization behavior.
   ===================================================================== */


/* ------------------------------------------------------------
   COUNT-UP ANIMATION FOR METRICS
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
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}


/* ------------------------------------------------------------
   CHART.JS GLOBAL DEFAULTS (Premium Duotone)
------------------------------------------------------------- */
Chart.defaults.font.family = "Nunito";
Chart.defaults.color = "#19350C";

Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle = "circle";

Chart.defaults.elements.line.borderCapStyle = "round";
Chart.defaults.elements.line.borderJoinStyle = "round";

Chart.defaults.datasets.line.fill = true;

Chart.defaults.scales.grid = {
    color: "rgba(64, 103, 104, 0.12)",
    drawBorder: false
};


/* ------------------------------------------------------------
   CO₂ BY TRANSPORT MODE — BAR CHART
------------------------------------------------------------- */
const modeCtx = document.getElementById("modeChart").getContext("2d");

const modeGradient = createGradient(
    modeCtx,
    "rgba(104, 125, 49, 0.9)",   // olive-green top
    "rgba(104, 125, 49, 0.3)"    // olive-green bottom
);

const modeChart = new Chart(modeCtx, {
    type: "bar",
    data: {
        labels: window.analyticsData.modeLabels,
        datasets: [{
            label: "CO₂ (kg)",
            data: window.analyticsData.modeData,
            backgroundColor: modeGradient,
            borderColor: "rgba(104, 125, 49, 1)",
            borderWidth: 2,
            borderRadius: 14,
            hoverBackgroundColor: "rgba(104, 125, 49, 1)"
        }]
    },
    options: {
        animation: {
            duration: 1600,
            easing: "easeOutQuart"
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: "rgba(64, 103, 104, 0.12)"
                }
            }
        }
    }
});


/* ------------------------------------------------------------
   MONTHLY CO₂ TREND — LINE CHART
------------------------------------------------------------- */
const monthCtx = document.getElementById("monthChart").getContext("2d");

const monthGradient = createGradient(
    monthCtx,
    "rgba(64, 103, 104, 0.8)",   // teal-dark top
    "rgba(64, 103, 104, 0.15)"   // teal-dark bottom
);

const monthChart = new Chart(monthCtx, {
    type: "line",
    data: {
        labels: window.analyticsData.monthLabels,
        datasets: [{
            label: "CO₂ (kg)",
            data: window.analyticsData.monthData,
            borderColor: "rgba(64, 103, 104, 1)",
            backgroundColor: monthGradient,
            borderWidth: 4,
            tension: 0.35,
            pointRadius: 5,
            pointBackgroundColor: "rgba(64, 103, 104, 1)",
            pointHoverRadius: 7
        }]
    },
    options: {
        animation: {
            duration: 1800,
            easing: "easeOutQuart"
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: "rgba(64, 103, 104, 0.12)"
                }
            }
        }
    }
});
