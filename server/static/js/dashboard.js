/* ===============================
   DASHBOARD JS — ÉTUDIANT C
   =============================== */

function loadDashboard() {

    // Vue d’ensemble
    fetch("/api/dashboard/overview")
        .then(response => response.json())
        .then(data => {
            document.getElementById("overview").innerText =
                `Agents actifs : ${data.agents} | Alertes : ${data.alerts}`;
        });

    // Agents actifs
    fetch("/api/dashboard/agents")
        .then(response => response.json())
        .then(data => {
            const ul = document.getElementById("agents");
            ul.innerHTML = "";
            data.forEach(agent => {
                const li = document.createElement("li");
                li.textContent = agent.agent_id ?? agent;
                ul.appendChild(li);
            });
        });

    // Alertes récentes
    fetch("/api/dashboard/alerts")
        .then(response => response.json())
        .then(data => {
            const ul = document.getElementById("alerts");
            ul.innerHTML = "";
            data.forEach(alert => {
                const li = document.createElement("li");
                li.className = alert.severity.toLowerCase();
                li.textContent =
                    `[${alert.severity}] ${alert.alert_type} ` +
                    `(${alert.source_ip} → ${alert.target_ip})`;
                ul.appendChild(li);
            });
        });
}

// Rafraîchissement automatique
setInterval(loadDashboard, 3000);
loadDashboard();
