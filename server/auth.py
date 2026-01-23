from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import datetime
import secrets

from server.config import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD_HASH,
    pwd_context,
    SESSION_TIMEOUT
)

router = APIRouter()

class SessionExpiredException(Exception):
    pass

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def require_login(request: Request) -> bool:
    session = request.session

    if "user" not in session or "last_activity" not in session:
        return False

    last_activity = datetime.fromisoformat(session["last_activity"])
    now = datetime.utcnow()

    if now - last_activity > SESSION_TIMEOUT:
        session.clear()
        raise SessionExpiredException()

    session["last_activity"] = now.isoformat()
    return True

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    with open("server/templates/login.html", encoding="utf-8") as f:
        html = f.read()

    msg = ""
    p = request.query_params
    if p.get("expired") == "1":
        msg = "Session expirée, veuillez vous reconnecter."
    elif p.get("error") == "1":
        msg = "Identifiants incorrects."
    elif p.get("error") == "csrf":
        msg = "Erreur CSRF détectée."

    return html.replace("{{MESSAGE}}", msg)

@router.get("/api/csrf-token")
def csrf_token(request: Request):
    token = secrets.token_hex(16)
    request.session["csrf_token"] = token
    return {"token": token}

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    if csrf_token != request.session.get("csrf_token"):
        return RedirectResponse("/login?error=csrf", status_code=302)

    if username != ADMIN_USERNAME or not verify_password(password, ADMIN_PASSWORD_HASH):
        return RedirectResponse("/login?error=1", status_code=302)

    request.session["user"] = username
    request.session["last_activity"] = datetime.utcnow().isoformat()
    return RedirectResponse("/dashboard", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
