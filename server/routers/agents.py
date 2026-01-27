from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from server.database import get_db
from server.models import Agent
from server.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class AgentResponse(BaseModel):
    id: int
    agent_id: str
    hostname: str
    ip_address: str
    status: str
    last_heartbeat: datetime
    location: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AgentResponse])
async def get_agents(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(Agent).all()


@router.get("/active", response_model=List[AgentResponse])
async def get_active_agents(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(Agent).filter(Agent.status == "active").all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent