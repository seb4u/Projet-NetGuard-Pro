from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Statistics

router = APIRouter()

# GET /dashboard - Interface web HTML (placeholder simple)
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_interface():
    return """
    <html>
        <head><title>Dashboard NetGuard</title></head>
        <body>
            <h1>Bienvenue sur le Dashboard NetGuard</h1>
            <p>Utilisez les métriques temps réel pour visualiser l'activité.</p>
        </body>
    </html>
    """

# GET /api/dashboard/metrics - Métriques temps réel
@router.get("/api/dashboard/metrics", summary="Métriques temps réel")
def dashboard_metrics(db: Session = Depends(get_db)):
    latest = db.query(Statistics).order_by(Statistics.timestamp.desc()).first()
    if not latest:
        raise HTTPException(status_code=404, detail="Aucune statistique trouvée.")
    return {
        "timestamp": latest.timestamp,
        "total_packets": latest.total_packets,
        "total_alerts": latest.total_alerts,
        "active_agents": latest.active_agents,
        "avg_packets_per_second": latest.avg_packets_per_second,
    }
