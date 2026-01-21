from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from server.services.collector import CollectorServer
from server.auth import router as auth_router, require_login, SessionExpiredException
from server.config import SESSION_SECRET_KEY

app = FastAPI(title="NetGuard Pro — Central Server")

# ================= SESSION MIDDLEWARE =================
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    https_only=False
)

# ================= EXCEPTION HANDLER =================
@app.exception_handler(SessionExpiredException)
async def session_expired_handler(request: Request, exc: SessionExpiredException):
    return RedirectResponse("/login?expired=1", status_code=302)

# ================= SERVICES =================
collector = CollectorServer()

# ================= STATIC =================
app.mount("/static", StaticFiles(directory="server/static"), name="static")

# ================= AUTH =================
app.include_router(auth_router)

# ================= DASHBOARD =================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    require_login(request)
    with open("server/templates/dashboard.html", encoding="utf-8") as f:
        return f.read()

@app.get("/api/dashboard/overview")
def overview(request: Request):
    require_login(request)
    return {
        "agents": len(collector.agents),
        "alerts": len(collector.recent_alerts)
    }

@app.get("/api/dashboard/agents")
def agents(request: Request):
    require_login(request)
    return [
        {"agent_id": aid, "status": data["status"]}
        for aid, data in collector.agents.items()
    ]

@app.get("/api/dashboard/alerts")
def alerts(request: Request):
    require_login(request)
    return collector.recent_alerts[-10:]
