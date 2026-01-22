from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ===== Routers existants (Étudiant A) =====
from traffic import router as traffic_router
from alerts import router as alerts_router
from receiver import router as receiver_router
from dashboard import router as dashboard_router

# ===== Modèles BD (Étudiant A) =====
from models import Agent, TrafficData, Alert, Statistics, Base

# ===== Sécurité / Authentification (Étudiant C) =====
# ⬇️ Nécessaire pour login, session, expiration
from auth import router as auth_router, require_login, SessionExpired
from config import SESSION_SECRET_KEY

import uuid

# ==================================================
# Initialisation de FastAPI
# ==================================================
app = FastAPI(title="NetGuard Pro - Central Server")

# ==================================================
# Middleware de session (AJOUT ÉTUDIANT C)
# 👉 OBLIGATOIRE pour que l’authentification fonctionne
# ==================================================
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,  # clé secrète des sessions
    same_site="lax",
    https_only=False  # True en production HTTPS
)

# ==================================================
# Configuration de la base de données (Étudiant A)
# ==================================================
DATABASE_URL = 'sqlite:///netguard.db'

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ==================================================
# Création automatique des tables
# 👉 indispensable pour un déploiement propre
# ==================================================
Base.metadata.create_all(bind=engine)

# ==================================================
# Fichiers statiques du dashboard (AJOUT ÉTUDIANT C)
# ==================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==================================================
# Gestion globale de l’expiration de session (Étudiant C)
# 👉 redirection vers /login au lieu de 401
# ==================================================
@app.exception_handler(SessionExpired)
def session_expired_handler(request: Request, exc):
    return RedirectResponse("/login?expired=1", status_code=302)

# ==================================================
# Authentification (Étudiant C)
# ==================================================
app.include_router(auth_router)

# ==================================================
# Page Dashboard sécurisée (Étudiant C)
# ==================================================
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    require_login(request)  # protection par session
    with open("templates/dashboard.html", encoding="utf-8") as f:
        return f.read()

# ==================================================
# Routers API (Étudiant A)
# ==================================================
app.include_router(traffic_router)
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alertes"])
app.include_router(receiver_router)

# Dashboard API (consommée par le front)
app.include_router(dashboard_router, tags=["Dashboard"])

# ==================================================
# ===== Gestion des AGENTS (Étudiant A)
# ==================================================

# Schéma Pydantic
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
        return {
            "message": "Agent enregistré avec succès",
            "agent_id": agent.agent_id
        }
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
        return db.query(Agent).all()
    finally:
        db.close()

# Endpoint 3: Statut d’un agent
@app.get("/api/agents/{agent_id}/status")
def get_agent_status(agent_id: str):
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent non trouvé")
        return {
            "agent_id": agent.agent_id,
            "status": agent.status,
            "last_heartbeat": agent.last_heartbeat
        }
    finally:
        db.close()
