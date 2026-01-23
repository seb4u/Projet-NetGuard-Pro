let agentsChart, severityChart, timelineChart;

/* ================= INIT CHARTS ================= */
function initCharts() {

    agentsChart = new Chart(document.getElementById("agentsChart"), {
        type: "bar",
        data: {
            labels: ["Agents actifs"],
            datasets: [{
                data: [0],
                backgroundColor: "#3498db"
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, precision: 0 } }
        }
    });

    severityChart = new Chart(document.getElementById("severityChart"), {
        type: "doughnut",
        data: {
            labels: ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: ["green", "orange", "darkorange", "red"]
            }]
        },
        options: {
            plugins: {
                legend: { display: false }
            }
        }
    });

    timelineChart = new Chart(document.getElementById("alertsTimeline"), {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Alertes",
                data: [],
                borderColor: "#9b59b6",
                tension: 0.3
            }]
        }
    });
}

/* ================= REFRESH ================= */
async function refreshDashboard() {
    try {
        const metrics = await fetch("/api/dashboard/metrics").then(r => r.json());
        const alerts = await fetch("/api/dashboard/alerts").then(r => r.json());

        document.getElementById("kpi-agents").innerText = metrics.active_agents;
        document.getElementById("kpi-alerts").innerText = metrics.total_alerts;

        agentsChart.data.datasets[0].data[0] = metrics.active_agents;
        agentsChart.update();

        let sev = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
        alerts.forEach(a => sev[a.severity]++);

        severityChart.data.datasets[0].data =
            [sev.LOW, sev.MEDIUM, sev.HIGH, sev.CRITICAL];
        severityChart.update();

        const now = new Date().toLocaleTimeString();
        timelineChart.data.labels.push(now);
        timelineChart.data.datasets[0].data.push(alerts.length);

        if (timelineChart.data.labels.length > 10) {
            timelineChart.data.labels.shift();
            timelineChart.data.datasets[0].data.shift();
        }
        timelineChart.update();

        const alertsUl = document.getElementById("alerts");
        alertsUl.innerHTML = "";

        alerts.slice(0, 10).forEach(a => {
            const li = document.createElement("li");
            li.className = a.severity.toLowerCase();
            li.textContent =
                `[${a.severity}] ${a.alert_type} (${a.source_ip} → ${a.target_ip})`;
            alertsUl.appendChild(li);
        });

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

/* ================= BOOT ================= */
initCharts();
refreshDashboard();
setInterval(refreshDashboard, 5000);
