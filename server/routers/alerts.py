from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from server.database import get_db
from server.models import Alert
from server.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    source_ip: str
    target_ip: Optional[str]
    description: Optional[str]
    timestamp: datetime
    acknowledged: bool
    resolved: bool
    agent_id: str

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    acknowledged: bool


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    return query.order_by(Alert.timestamp.desc()).all()


@router.get("/recent", response_model=List[AlertResponse])
async def get_recent_alerts(limit: int = 10, db: Session = Depends(get_db),
                            current_user: str = Depends(get_current_user)):
    return db.query(Alert).order_by(Alert.timestamp.desc()).limit(limit).all()


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db),
                            current_user: str = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    alert.acknowledged_by = current_user
    db.commit()
    return {"status": "acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True
    db.commit()
    return {"status": "resolved"}