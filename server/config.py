from passlib.context import CryptContext
from datetime import timedelta

# ================= AUTH ADMIN =================
ADMIN_USERNAME = "admin"

# Mot de passe réel : netguard2026
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ADMIN_PASSWORD_HASH = pwd_context.hash("netguard2026")

# ================= SESSION =================
SESSION_SECRET_KEY = "CHANGE_ME_SUPER_SECRET_KEY_2026"
SESSION_TIMEOUT = timedelta(minutes=15)
