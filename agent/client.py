import socket
import json
import time


class SocketClient:
    def __init__(self, server_host, server_port, agent_id):
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id
        self.socket = None
        self.connected = False

    def connect(self):
        """Connexion au serveur TCP"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"[+] Connecté au serveur {self.server_host}:{self.server_port}")
        except Exception as e:
            print(f"[!] Erreur de connexion : {e}")
            self.connected = False

    def disconnect(self):
        """Fermer la connexion"""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("[*] Déconnecté du serveur")

    def send_message(self, message: dict):
        """Envoie un message JSON au serveur"""
        if not self.connected:
            print("[!] Non connecté au serveur, tentative de reconnexion...")
            self.connect()

        try:
            data = json.dumps(message).encode("utf-8")
            self.socket.sendall(data)

            # Réception de la réponse
            response = self.socket.recv(4096).decode("utf-8")
            if response:
                return json.loads(response)

        except Exception as e:
            print(f"[!] Erreur d’envoi : {e}")
            self.connected = False
            return None

    def register(self):
        """Enregistrer l’agent auprès du serveur"""
        message = {
            "type": "REGISTER",
            "agent_id": self.agent_id
        }
        response = self.send_message(message)
        if response:
            print(f"[+] Agent enregistré : {response}")

    def send_heartbeat(self):
        """Envoyer un heartbeat"""
        message = {
            "type": "HEARTBEAT",
            "agent_id": self.agent_id
        }
        self.send_message(message)

    def send_alert(self, alert_data):
        """Envoyer une alerte"""
        message = {
            "type": "ALERT",
            "agent_id": self.agent_id,
            "alert": alert_data
        }
        self.send_message(message)

    def send_statistics(self, stats):
        """Envoyer des statistiques"""
        message = {
            "type": "STATISTICS",
            "agent_id": self.agent_id,
            "data": stats
        }
        self.send_message(message)
