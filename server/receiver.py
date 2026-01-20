from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import Alert
from datetime import datetime

router = APIRouter()

# === Schémas ===
class AlertData(BaseModel):
    alert_type: str
    severity: str
    source_ip: str
    target_ip: str
    description: str
    details: str

class AlertMessage(BaseModel):
    type: str  # Doit être "ALERT"
    agent_id: str
    alert: AlertData

# === Endpoint ===
@router.post("/api/alerts/receive", status_code=status.HTTP_201_CREATED)
def receive_alert(payload: AlertMessage, db: Session = Depends(get_db)):
    if payload.type != "ALERT":
        raise HTTPException(status_code=400, detail="Type de message invalide")

    new_alert = Alert(
        alert_type=payload.alert.alert_type,
        severity=payload.alert.severity,
        source_ip=payload.alert.source_ip,
        target_ip=payload.alert.target_ip,
        description=payload.alert.description,
        details=payload.alert.details,
        timestamp=datetime.utcnow(),
        acknowledged=False,
        resolved=False
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return {"message": "Alerte reçue avec succès", "id": new_alert.id}
