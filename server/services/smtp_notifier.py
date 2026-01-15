import smtplib
from email.message import EmailMessage

def send_email_alert(alert):
    msg = EmailMessage()
    msg["Subject"] = f"[ALERTE {alert['severity']}] {alert['alert_type']}"
    msg["From"] = "ids@local"
    msg["To"] = "admin@local"

    msg.set_content(f"""
Alerte détectée :

Type : {alert['alert_type']}
Gravité : {alert['severity']}
Source : {alert['source_ip']}
Cible : {alert['target_ip']}
""")

    # SMTP local (exemple)
    try:
        with smtplib.SMTP("localhost") as server:
            server.send_message(msg)
    except Exception:
        pass
