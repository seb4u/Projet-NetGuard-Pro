import smtplib
from email.message import EmailMessage

SMTP_HOST = "localhost"
SMTP_PORT = 25
MAIL_FROM = "netguard@localhost"
MAIL_TO = ["admin@localhost"]


def send_email_alert(alert: dict):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"[NetGuard] {alert['severity']} - {alert['alert_type']}"
        msg["From"] = MAIL_FROM
        msg["To"] = ", ".join(MAIL_TO)

        msg.set_content(f"""
ALERTE DE SÉCURITÉ

Type      : {alert['alert_type']}
Gravité   : {alert['severity']}
Source IP : {alert['source_ip']}
Cible IP  : {alert['target_ip']}
Date      : {alert['timestamp']}

Détails :
{alert.get('details', {})}
""")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
            server.send_message(msg)

    except Exception as e:
        print(f"[SMTP] Erreur : {e}")
