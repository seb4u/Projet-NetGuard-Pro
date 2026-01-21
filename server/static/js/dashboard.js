async function refresh() {
    const overview = await fetch("/api/dashboard/overview").then(r => r.json());
    document.getElementById("overview").innerText =
        `Agents actifs : ${overview.agents} | Alertes : ${overview.alerts}`;

    const agents = await fetch("/api/dashboard/agents").then(r => r.json());
    const agentsUl = document.getElementById("agents");
    agentsUl.innerHTML = "";
    agents.forEach(a => {
        const li = document.createElement("li");
        li.textContent = `${a.agent_id} — ${a.status}`;
        agentsUl.appendChild(li);
    });

    const alerts = await fetch("/api/dashboard/alerts").then(r => r.json());
    const alertsUl = document.getElementById("alerts");
    alertsUl.innerHTML = "";
    alerts.forEach(a => {
        const li = document.createElement("li");
        li.className = a.severity.toLowerCase();
        li.textContent = `[${a.severity}] ${a.alert_type} (${a.source_ip} → ${a.target_ip})`;
        alertsUl.appendChild(li);
    });
}

setInterval(refresh, 3000);
refresh();
