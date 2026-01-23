import socket
import threading
import json
from datetime import datetime, timedelta
import requests

from server.services.smtp_notifier import send_email_alert
from server.database.bridge import (
    upsert_agent,
    update_agent_heartbeat,
    save_alert
)

HOST = "0.0.0.0"
PORT = 9000
HEARTBEAT_TIMEOUT = 30


class CollectorServer:
    def __init__(self):
        self.agents = {}
        self.recent_alerts = []

        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.monitor_agents, daemon=True).start()

    # ---------------- SOCKET SERVER ----------------
    def start_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((HOST, PORT))
        sock.listen(10)
        print(f"[COLLECTOR] Listening on {HOST}:{PORT}")

        while True:
            client, _ = sock.accept()
            threading.Thread(
                target=self.handle_client,
                args=(client,),
                daemon=True
            ).start()

    def handle_client(self, client):
        while True:
            data = client.recv(4096)
            if not data:
                break
            try:
                message = json.loads(data.decode())
                self.dispatch(message)
            except Exception:
                pass

    # ---------------- ROUTER ----------------
    def dispatch(self, msg):
        msg_type = msg.get("type")

        if msg_type == "REGISTER":
            self.register_agent(msg)
        elif msg_type == "HEARTBEAT":
            self.handle_heartbeat(msg)
        elif msg_type == "ALERT":
            self.handle_alert(msg)

    # ---------------- HANDLERS ----------------
    def register_agent(self, msg):
        agent_id = msg["agent_id"]
        self.agents[agent_id] = {
            "last_heartbeat": datetime.utcnow(),
            "status": "ONLINE"
        }
        upsert_agent(agent_id)

    def handle_heartbeat(self, msg):
        agent_id = msg["agent_id"]
        if agent_id in self.agents:
            self.agents[agent_id]["last_heartbeat"] = datetime.utcnow()
            self.agents[agent_id]["status"] = "ONLINE"
            update_agent_heartbeat(agent_id)

    def handle_alert(self, msg):
        alert = msg["alert"]
        self.recent_alerts.append(alert)

        if alert["severity"] in ("HIGH", "CRITICAL"):
            send_email_alert(alert)

        save_alert(msg["agent_id"], alert)

        # Forward to API Étudiant A (optionnel)
        try:
            requests.post(
                "http://localhost:8000/api/alerts/receive",
                json=msg,
                timeout=2
            )
        except Exception:
            pass

    # ---------------- HEARTBEAT MONITOR ----------------
    def monitor_agents(self):
        while True:
            now = datetime.utcnow()
            for agent_id, data in self.agents.items():
                if now - data["last_heartbeat"] > timedelta(seconds=HEARTBEAT_TIMEOUT):
                    data["status"] = "OFFLINE"
