from datetime import datetime
import json

from server.database.session import SessionLocal
from server.database.models import Agent, Alert

def upsert_agent(agent_id: str, status="ONLINE"):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter_by(agent_id=agent_id).first()
        if agent:
            agent.status = status
            agent.last_heartbeat = datetime.utcnow()
        else:
            db.add(Agent(agent_id=agent_id, status=status))
        db.commit()
    finally:
        db.close()


def update_agent_heartbeat(agent_id: str):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter_by(agent_id=agent_id).first()
        if agent:
            agent.last_heartbeat = datetime.utcnow()
            agent.status = "ONLINE"
            db.commit()
    finally:
        db.close()


def save_alert(agent_id: str, alert: dict):
    db = SessionLocal()
    try:
        db_alert = Alert(
            alert_type=alert["alert_type"],
            severity=alert["severity"],
            source_ip=alert["source_ip"],
            target_ip=alert["target_ip"],
            description="",
            details=json.dumps(alert.get("details", {})),
            timestamp=datetime.fromisoformat(alert["timestamp"]),
            acknowledged=False,
            resolved=False
        )
        db.add(db_alert)
        db.commit()
    finally:
        db.close()
