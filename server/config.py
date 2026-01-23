from passlib.context import CryptContext
from datetime import timedelta

# ================= AUTH ADMIN =================
ADMIN_USERNAME = "admin"

# Mot de passe réel : netguard2026
# Hash bcrypt valide
ADMIN_PASSWORD_HASH = "$2b$12$aIZ98olaWCn5.leW1UkF0uprpkO1NqOb90n047A9g9uxE5s5fXj9K"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ================= SESSION =================
SESSION_SECRET_KEY = "CHANGE_ME_SUPER_SECRET_KEY_2026"
SESSION_TIMEOUT = timedelta(minutes=15)
