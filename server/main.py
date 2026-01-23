from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

from server.models import Alert, Statistics, Base
from auth import router as auth_router, require_login, SessionExpiredException
from server.config import SESSION_SECRET_KEY

# ==================================================
# Base directory
# ==================================================
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "netguard.db"

# ==================================================
# App
# ==================================================
app = FastAPI(title="NetGuard Pro - Dashboard")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax"
)

# ==================================================
# Database
# ==================================================
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================================================
# Static files
# ==================================================
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# ==================================================
# Auth
# ==================================================
app.include_router(auth_router)

# ==================================================
# Pages
# ==================================================
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    try:
        if not require_login(request):
            return RedirectResponse("/login")
    except SessionExpiredException:
        return RedirectResponse("/login?expired=1")

    with open(BASE_DIR / "templates" / "dashboard.html", encoding="utf-8") as f:
        return f.read()

# ==================================================
# API - Dashboard
# ==================================================
@app.get("/api/dashboard/overview")
def dashboard_overview(db: Session = Depends(get_db)):
    stat = db.query(Statistics).order_by(Statistics.timestamp.desc()).first()
    return {
        "agents": stat.active_agents if stat else 0,
        "alerts": stat.total_alerts if stat else 0
    }

@app.get("/api/dashboard/agents")
def dashboard_agents(db: Session = Depends(get_db)):
    return []

@app.get("/api/dashboard/alerts")
def dashboard_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()
    return [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "source_ip": a.source_ip,
            "target_ip": a.target_ip,
            "timestamp": a.timestamp.isoformat()
        }
        for a in alerts
    ]

@app.get("/api/dashboard/metrics")
def dashboard_metrics(db: Session = Depends(get_db)):
    stat = db.query(Statistics).order_by(Statistics.timestamp.desc()).first()
    return {
        "active_agents": stat.active_agents if stat else 0,
        "total_alerts": stat.total_alerts if stat else 0,
        "total_packets": stat.total_packets if stat else 0,
        "avg_packets_per_second": stat.avg_packets_per_second if stat else 0
    }
