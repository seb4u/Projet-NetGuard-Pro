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

# ================= EXCEPTION =================
class SessionExpiredException(Exception):
    pass

# ================= UTILS =================
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def require_login(request: Request):
    session = request.session

    if "user" not in session or "last_activity" not in session:
        raise SessionExpiredException()

    last_activity = datetime.fromisoformat(session["last_activity"])
    now = datetime.utcnow()

    if now - last_activity > SESSION_TIMEOUT:
        session.clear()
        raise SessionExpiredException()

    session["last_activity"] = now.isoformat()

# ================= ROUTES =================
@router.get("/login", response_class=HTMLResponse)
def login_page():
    with open("server/templates/login.html", encoding="utf-8") as f:
        return f.read()

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

    if username != ADMIN_USERNAME:
        return RedirectResponse("/login?error=1", status_code=302)

    if not verify_password(password, ADMIN_PASSWORD_HASH):
        return RedirectResponse("/login?error=1", status_code=302)

    request.session["user"] = username
    request.session["last_activity"] = datetime.utcnow().isoformat()

    return RedirectResponse("/dashboard", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
