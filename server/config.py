#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration centralisée NetGuard Pro
UVCI - Master Cybersécurité & IoT
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Configuration centralisée avec support SSL/TLS pour Gmail
    """

    # ============================================================
    # BASE DE DONNÉES
    # ============================================================
    DATABASE_URL = "sqlite:///./netguard.db"

    # ============================================================
    # SÉCURITÉ & AUTHENTIFICATION
    # ============================================================
    SECRET_KEY = "netguard-secret-key-2026-uvci-cybersecurity-master-cio"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

    # Identifiants Administrateur
    ADMIN_USERNAME = "admin"
    # Hash bcrypt pour "admin123"
    ADMIN_PASSWORD = "$2b$12$3YDlEyXMPeiWBdQvLr2dvO3/UyZZV3fudPcC9t3A/4dfrsirHbivO"

    # ============================================================
    # CONFIGURATION EMAIL (SMTP GMAIL)
    # ============================================================
    # IMPORTANT: Pour Gmail, utilisez:
    # - Port 465 avec SSL = True (recommandé)
    # - OU Port 587 avec SSL = False (TLS/STARTTLS)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465  # 465 pour SSL, 587 pour TLS/STARTTLS
    SMTP_USE_SSL = True  # True = SSL (port 465), False = TLS (port 587)

    # ⚠️ CRITIQUE: Utilisez un "Mot de passe d'application" Gmail à 16 caractères
    # Comment en générer un: https://myaccount.google.com/apppasswords
    SENDER_EMAIL = "kevinleroi96@gmail.com"
    SENDER_PASSWORD = "PROGRAMME1996"  # À remplacer par mot de passe d'application

    # ============================================================
    # CONFIGURATION AGENTS
    # ============================================================
    HEARTBEAT_INTERVAL = 30
    AGENT_TIMEOUT = 300

    # ============================================================
    # CHEMINS & FICHIERS
    # ============================================================
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, "server", "static")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "server", "templates")


# Instance unique
settings = Settings()

# ============================================================
# VÉRIFICATION AU DÉMARRAGE
# ============================================================
if __name__ == "__main__":
    try:
        import bcrypt

        # Test immédiat du hash admin
        test_result = bcrypt.checkpw(
            b"admin123",
            settings.ADMIN_PASSWORD.encode('utf-8')
        )

        if test_result:
            print("✅ SUCCÈS: Le hash fonctionne avec 'admin123'")
        else:
            print("❌ ÉCHEC: Hash invalide")
            print("🔧 Génération d'un nouveau hash valide:")
            new_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            print(f'ADMIN_PASSWORD = "{new_hash}"')

        # Test configuration SMTP
        print(f"\n📧 Configuration SMTP:")
        print(f"   Serveur: {settings.SMTP_SERVER}:{settings.SMTP_PORT}")
        print(f"   SSL: {settings.SMTP_USE_SSL}")
        print(f"   Email: {settings.SENDER_EMAIL}")

        if settings.SENDER_PASSWORD == "PROGRAMME1996":
            print("\n⚠️  AVERTISSEMENT: Vous utilisez le mot de passe par défaut!")
            print("   Pour Gmail, générez un mot de passe d'application à 16 caractères.")
            print("   URL: https://myaccount.google.com/apppasswords")
        else:
            print("✅ Mot de passe SMTP personnalisé détecté")

    except Exception as e:
        print(f"❌ Erreur: {e}")