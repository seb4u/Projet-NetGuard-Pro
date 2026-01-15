from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import TrafficData, Statistics
from datetime import datetime
from database import get_db

router = APIRouter()

# POST /api/traffic/submit : Soumettre des données de trafic
@router.post("/api/traffic/submit")
def submit_traffic(data: dict, db: Session = Depends(get_db)):
    try:
        traffic = TrafficData(
            agent_id=data["agent_id"],
            timestamp=datetime.now(),
            source_ip=data["source_ip"],
            dest_ip=data["dest_ip"],
            protocol=data["protocol"],
            port=data["port"],
            packet_size=data["packet_size"],
            flags=data.get("flags", "")
        )
        db.add(traffic)
        db.commit()
        db.refresh(traffic)
        return {"message": "Données de trafic enregistrées", "id": traffic.id}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Champ manquant: {e}")

# GET /api/traffic/stats : Statistiques du trafic
@router.get("/api/traffic/stats")
def get_traffic_stats(db: Session = Depends(get_db)):
    stats = db.query(Statistics).order_by(Statistics.timestamp.desc()).first()
    if not stats:
        raise HTTPException(status_code=404, detail="Aucune statistique trouvée")
    
    return {
        "timestamp": stats.timestamp,
        "total_packets": stats.total_packets,
        "total_alerts": stats.total_alerts,
        "active_agents": stats.active_agents,
        "avg_packets_per_second": stats.avg_packets_per_second,
    }
