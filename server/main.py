#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetGuard Pro - Serveur FastAPI
Version 2.6.0 avec gestion d'événements lifespan
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import threading
from contextlib import asynccontextmanager

# Database et Routing
from server.database import engine, Base
from server.routers import agents, alerts, auth, dashboard
from server.services.collector import get_collector


# ─────────────────────────────────────────────────────────────────────────────
# LIFESPAN MANAGER (Remplace les deprecated @app.on_event)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application (startup/shutdown)"""
    # [STARTUP] Démarrage du collecteur TCP
    collector = get_collector()
    thread = threading.Thread(target=collector.start, daemon=True)
    thread.start()
    print("✅ Serveur de collecte démarré sur le port 9999")

    yield  # Application en cours d'exécution

    # [SHUTDOWN] Arrêt propre du collecteur
    collector.stop()
    print("🛑 Serveur de collecte arrêté")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION FASTAPI
# ─────────────────────────────────────────────────────────────────────────────

# Création des tables SQLAlchemy
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NetGuard Pro",
    description="Plateforme Distribuée de Supervision et Détection d'Intrusions",
    version="2.6.0",
    lifespan=lifespan  # Nouveau système d'événements
)

# CORS - Configuration des origines autorisées
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files et Templates
app.mount("/static", StaticFiles(directory="server/static"), name="static")
templates = Jinja2Templates(directory="server/templates")

# Inclusion des routers API
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES WEB
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirection vers la page de login"""
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de connexion SOC"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Page principale du dashboard SOC"""
    # Le paramètre request n'est pas utilisé directement mais est requis par Jinja2
    return templates.TemplateResponse("dashboard.html", {"request": {"url": "http://localhost:8000/dashboard"}})


@app.get("/api/health")
async def health_check():
    """Endpoint de health check pour monitoring"""
    collector = get_collector()
    return {
        "status": "healthy",
        "collector_active": collector.running if collector else False,
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# LANCEMENT DIRECT (pour développement)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)