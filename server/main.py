from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from server.services.collector import CollectorServer

app = FastAPI(title="NetGuard Pro — Central Server")

collector = CollectorServer()

# Static files
app.mount("/static", StaticFiles(directory="server/static"), name="static")

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("server/templates/dashboard.html", encoding="utf-8") as f:
        return f.read()

# Dashboard API
@app.get("/api/dashboard/overview")
def overview():
    return {
        "agents": len(collector.agents),
        "alerts": len(collector.recent_alerts)
    }

@app.get("/api/dashboard/agents")
def agents():
    return [
        {"agent_id": aid, "status": data["status"]}
        for aid, data in collector.agents.items()
    ]

@app.get("/api/dashboard/alerts")
def alerts():
    return collector.recent_alerts[-10:]
