import socket
import threading
import json
from datetime import datetime, timedelta
from server.services.smtp_notifier import send_email_alert

HOST = "0.0.0.0"
PORT = 9000
HEARTBEAT_TIMEOUT = 30  # secondes

class CollectorServer:
    def __init__(self):
        self.agents = {}
        self.recent_alerts = []

        thread = threading.Thread(target=self.start_server, daemon=True)
        thread.start()

        monitor = threading.Thread(target=self.monitor_agents, daemon=True)
        monitor.start()

    # -------------------------------
    # Socket server
    # -------------------------------
    def start_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((HOST, PORT))
        sock.listen(5)

        while True:
            client, _ = sock.accept()
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def handle_client(self, client):
        while True:
            data = client.recv(4096)
            if not data:
                break

            message = json.loads(data.decode())
            self.dispatch(message)

    # -------------------------------
    # Message router
    # -------------------------------
    def dispatch(self, msg):
        msg_type = msg.get("type")

        if msg_type == "REGISTER":
            self.handle_register(msg)
        elif msg_type == "HEARTBEAT":
            self.handle_heartbeat(msg)
        elif msg_type == "ALERT":
            self.handle_alert(msg)

    # -------------------------------
    # Handlers
    # -------------------------------
    def handle_register(self, msg):
        self.agents[msg["agent_id"]] = {
            "last_heartbeat": datetime.now(),
            "status": "ONLINE"
        }

    def handle_heartbeat(self, msg):
        if msg["agent_id"] in self.agents:
            self.agents[msg["agent_id"]]["last_heartbeat"] = datetime.now()

    def handle_alert(self, msg):
        alert = msg["alert"]
        self.recent_alerts.append(alert)

        if alert["severity"] in ("HIGH", "CRITICAL"):
            send_email_alert(alert)

        # ===============================
        # INTÉGRATION BD — ÉTUDIANT A
        # ===============================
        """
        from server.database.session import SessionLocal
        from server.database.models import Alert

        db = SessionLocal()
        db_alert = Alert(
            alert_type=alert["alert_type"],
            severity=alert["severity"],
            source_ip=alert["source_ip"],
            target_ip=alert["target_ip"],
            details=json.dumps(alert["details"]),
            timestamp=datetime.fromisoformat(alert["timestamp"])
        )
        db.add(db_alert)
        db.commit()
        db.close()
        """

    # -------------------------------
    # Heartbeat monitor
    # -------------------------------
    def monitor_agents(self):
        while True:
            now = datetime.now()
            for agent_id, data in list(self.agents.items()):
                if now - data["last_heartbeat"] > timedelta(seconds=HEARTBEAT_TIMEOUT):
                    data["status"] = "OFFLINE"
