#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de notification par email avec support SSL/TLS
Supporte Gmail sur port 465 (SSL) ou 587 (TLS/STARTTLS)
"""

import smtplib
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
import jinja2
import os
from datetime import datetime

from server.config import settings

logger = logging.getLogger(__name__)


class AlertNotifier:
    """Service de notification d'alertes de sécurité par email"""

    def __init__(self, template_path: Optional[str] = None):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_use_ssl = getattr(settings, 'SMTP_USE_SSL', True)  # SSL par défaut
        self.sender_email = settings.SENDER_EMAIL
        self.password = settings.SENDER_PASSWORD

        # Configuration Jinja2
        template_dir = template_path or os.path.join(
            settings.BASE_DIR, "server", "templates"
        )
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

        # Vérification configuration
        if not all([self.smtp_server, self.sender_email, self.password]):
            logger.error("⚠️ Configuration email incomplète!")
            print("⚠️  AVERTISSEMENT: Vérifier SMTP_SERVER, SENDER_EMAIL, SENDER_PASSWORD dans config.py")

    def _check_smtp_auth(self) -> bool:
        """Teste la connexion SMTP avec le protocole approprié"""
        try:
            if self.smtp_use_ssl:
                # SSL direct sur port 465 (recommandé)
                logger.debug(f"Connexion SMTP_SSL sur {self.smtp_server}:{self.smtp_port}")
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.sender_email, self.password)
            else:
                # TLS via STARTTLS sur port 587
                logger.debug(f"Connexion SMTP avec STARTTLS sur {self.smtp_server}:{self.smtp_port}")
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()  # Upgrade vers TLS
                    server.login(self.sender_email, self.password)

            logger.info("✅ Authentification SMTP réussie")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Échec authentification: {e}")
            print("\n🔧 SOLUTION POUR GMAIL:")
            print("   1. Activez la validation en 2 étapes")
            print("   2. Générez un mot de passe d'application: https://myaccount.google.com/apppasswords")
            print("   3. Mettez à jour SENDER_PASSWORD dans config.py")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur connexion SMTP: {e}")
            print(f"\n🔧 Problème de connexion ({'SSL' if self.smtp_use_ssl else 'TLS'}):")
            print(f"   Port: {self.smtp_port}")
            print(f"   Serveur: {self.smtp_server}")
            print("   Vérifiez votre pare-feu/antivirus")
            return False

    def _validate_alert_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données d'alerte avant envoi"""
        required_fields = ['type', 'severity', 'source_ip', 'target_ip', 'agent_id']
        if not all(field in data for field in required_fields):
            logger.error(f"Données d'alerte invalides: champs requis manquants")
            return False

        if data['severity'] not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            logger.error(f"Sévérité invalide: {data['severity']}")
            return False

        return True

    async def send_alert(
            self,
            alert_data: Dict[str, Any],
            recipients: Optional[List[str]] = None,
            max_retries: int = 3
    ) -> bool:
        """Envoie une alerte par email avec retry mechanism et support SSL/TLS"""
        if not self._validate_alert_data(alert_data):
            return False

        if recipients is None:
            recipients = [self.sender_email]

        if 'timestamp' not in alert_data:
            alert_data['timestamp'] = datetime.now().isoformat()

        subject = f"🚨 [NETGUARD-{alert_data['severity']}] {alert_data['type']} - Agent {alert_data['agent_id']}"

        try:
            template = self.jinja_env.get_template("email_alert.html")
            html_content = template.render(**alert_data)
        except Exception as e:
            logger.error(f"Erreur rendu template: {e}")
            html_content = self._generate_fallback_html(alert_data)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"NetGuard Pro SOC <{self.sender_email}>"
        message["To"] = ", ".join(recipients)

        part = MIMEText(html_content, "html")
        message.attach(part)

        # Tentatives d'envoi avec backoff exponentiel
        for attempt in range(max_retries):
            try:
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    None,
                    self._send_email_sync,
                    message,
                    recipients
                )
                if success:
                    logger.info(f"✅ Email alerte envoyé ({alert_data['type']}/{alert_data['severity']})")
                    return True
            except Exception as e:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée: {e}, retry dans {wait_time}s")
                await asyncio.sleep(wait_time)

        logger.error(f"❌ Échec envoi email après {max_retries} tentatives")
        return False

    def _generate_fallback_html(self, data: Dict[str, Any]) -> str:
        """Génère un HTML de secours si le template Jinja2 échoue"""
        return f"""
        <html>
        <body style="font-family: monospace;">
        <h2>🚨 ALERTE NETGUARD PRO</h2>
        <p><strong>Type:</strong> {data.get('type', 'N/A')}</p>
        <p><strong>Sévérité:</strong> {data.get('severity', 'N/A')}</p>
        <p><strong>Source:</strong> {data.get('source_ip', 'N/A')}</p>
        <p><strong>Cible:</strong> {data.get('target_ip', 'N/A')}</p>
        <p><strong>Agent:</strong> {data.get('agent_id', 'N/A')}</p>
        <p><strong>Heure:</strong> {data.get('timestamp', 'N/A')}</p>
        </body>
        </html>
        """

    def _send_email_sync(self, message, recipients) -> bool:
        """Envoi synchrone avec support SSL ou TLS"""
        try:
            logger.debug(
                f"📧 Envoi email à {recipients} via {self.smtp_server}:{self.smtp_port} ({'SSL' if self.smtp_use_ssl else 'TLS'})")

            if self.smtp_use_ssl:
                # SSL direct (port 465)
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.sender_email, self.password)
                    server.sendmail(self.sender_email, recipients, message.as_string())
            else:
                # TLS via STARTTLS (port 587)
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.sender_email, self.password)
                    server.sendmail(self.sender_email, recipients, message.as_string())

            logger.info(f"✅ Email envoyé avec succès à {len(recipients)} destinataire(s)")
            return True

        except Exception as e:
            logger.error(f"❌ Erreur envoi: {e}")
            raise  # Re-raise pour le retry mechanism


# Instance singleton
_notifier_instance = None


def get_notifier() -> AlertNotifier:
    """Factory pour obtenir l'instance singleton du notifier"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = AlertNotifier()
    return _notifier_instance


# Alias pour compatibilité ascendante
notifier = get_notifier()


# ==========================
# Fonctions de test
# ==========================

async def test_email(severity: str = "HIGH", alert_type: str = "TEST_EMAIL"):
    """Teste l'envoi d'email avec différentes sévérités"""
    print(f"📧 Test d'envoi d'email (sévérité: {severity})...")

    # Test la connexion SMTP d'abord
    notifier = get_notifier()
    if not notifier._check_smtp_auth():
        print("❌ Échec authentification SMTP - Test annulé")
        return False

    test_alert = {
        "type": alert_type,
        "severity": severity,
        "source_ip": f"192.168.1.{hash(alert_type) % 255}",
        "target_ip": "192.168.1.100",
        "agent_id": "test-critical-agent",
        "timestamp": datetime.now().isoformat(),
        "description": f"Test d'alerte de sévérité {severity} - Vérifiez votre boîte mail",
        "details": {
            "attack_vector": "Test automatique",
            "confidence": "100%",
            "requires_action": True,
            "test_mode": True,
            "smtp_config": {
                "port": settings.SMTP_PORT,
                "ssl": settings.SMTP_USE_SSL,
                "server": settings.SMTP_SERVER
            }
        }
    }

    success = await notifier.send_alert(test_alert)

    if success:
        print(f"✅ Test {severity} réussi! Vérifiez votre boîte mail dans 30s.")
        await asyncio.sleep(30)
    else:
        print(f"❌ Test {severity} échoué. Vérifiez logs et configuration SMTP.")
        print("🔧 Conseils: vérifiez pare-feu, antivirus, et mot de passe d'application")

    return success


async def test_all_severities():
    """Teste tous les niveaux de sévérité"""
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    results = {}

    for severity in severities:
        print(f"\n{'=' * 50}")
        print(f"Testing severity: {severity}")
        print(f"{'=' * 50}")

        results[severity] = await test_email(severity=severity, alert_type=f"TEST_{severity}")
        await asyncio.sleep(2)

    print("\n📊 RÉSULTATS DES TESTS:")
    for severity, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {severity:10} : {status}")

    return all(results.values())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test le service de notification email")
    parser.add_argument("--severity", "-s", default="HIGH",
                        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                        help="Niveau de sévérité à tester")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Tester tous les niveaux de sévérité")

    args = parser.parse_args()

    if args.all:
        asyncio.run(test_all_severities())
    else:
        asyncio.run(test_email(severity=args.severity))