from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from traffic import router as traffic_router
from models import Agent, TrafficData, Alert, Statistics, Base
from alerts import router as alerts_router
from dashboard import router as dashboard_router
import uuid

# Initialisation de FastAPI
app = FastAPI()

app.include_router(traffic_router)
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alertes"])
app.include_router(dashboard_router, tags=["Dashboard"])

# Configuration de la base de données
DATABASE_URL = 'sqlite:///netguard.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Schémas Pydantic
class AgentRegisterRequest(BaseModel):
    hostname: str
    ip_address: str

# Endpoint 1: Enregistrer un agent
@app.post("/api/agents/register")
def register_agent(data: AgentRegisterRequest):
    db = SessionLocal()
    try:
        agent = Agent(
            agent_id=str(uuid.uuid4()),
            hostname=data.hostname,
            ip_address=data.ip_address,
            status="active",
            created_at=datetime.now(),
            last_heartbeat=datetime.now()
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return {"message": "Agent enregistré avec succès", "agent_id": agent.agent_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Endpoint 2: Lister tous les agents
@app.get("/api/agents")
def list_agents():
    db = SessionLocal()
    try:
        agents = db.query(Agent).all()
        return agents
    finally:
        db.close()

# Endpoint 3: Récupérer le statut d'un agent
@app.get("/api/agents/{agent_id}/status")
def get_agent_status(agent_id: str):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent non trouvé")
        return {"agent_id": agent.agent_id, "status": agent.status, "last_heartbeat": agent.last_heartbeat}
    finally:
        db.close()
