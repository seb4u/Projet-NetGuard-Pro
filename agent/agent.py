import socket
import json
import time
import threading
import random
from datetime import datetime


class TestAgent:
    def __init__(self, agent_id, server_host="localhost", server_port=9999):
        self.agent_id = agent_id
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.packet_count = 0

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_host, self.server_port))
        print(f"[AGENT {self.agent_id}] Connecté au serveur")

    def register(self):
        msg = {
            "type": "REGISTER",
            "agent_id": self.agent_id,
            "hostname": f"workstation-{self.agent_id}",
            "location": "Salle Serveurs A"
        }
        self.send_message(msg)
        response = self.socket.recv(1024).decode('utf-8')
        print(f"[AGENT {self.agent_id}] Enregistrement: {response}")

    def send_message(self, msg):
        self.socket.send(json.dumps(msg).encode('utf-8'))

    def heartbeat_loop(self):
        while self.running:
            msg = {
                "type": "HEARTBEAT",
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }
            self.send_message(msg)
            time.sleep(30)

    def simulate_traffic(self):
        """Simule du trafic réseau normal"""
        while self.running:
            self.packet_count += random.randint(1, 10)

            # Envoi statistiques toutes les 10 secondes
            if self.packet_count % 50 == 0:
                msg = {
                    "type": "STATISTICS",
                    "agent_id": self.agent_id,
                    "data": {
                        "total_packets": self.packet_count,
                        "packets_per_second": random.uniform(10, 100),
                        "cpu_usage": random.uniform(10, 60),
                        "memory_usage": random.uniform(20, 80)
                    }
                }
                self.send_message(msg)

            time.sleep(1)

    def simulate_attack(self, attack_type="PORT_SCAN"):
        """Simule une attaque pour tester la détection"""
        if attack_type == "PORT_SCAN":
            alert = {
                "type": "ALERT",
                "agent_id": self.agent_id,
                "alert": {
                    "type": "PORT_SCAN",
                    "severity": "HIGH",
                    "source_ip": f"192.168.1.{random.randint(10, 50)}",
                    "target_ip": "192.168.1.100",
                    "description": "Scan de ports détecté",
                    "details": "Plus de 20 ports scannés en moins de 60 secondes",
                    "timestamp": datetime.now().isoformat()
                }
            }
        elif attack_type == "SYN_FLOOD":
            alert = {
                "type": "ALERT",
                "agent_id": self.agent_id,
                "alert": {
                    "type": "SYN_FLOOD",
                    "severity": "CRITICAL",
                    "source_ip": f"10.0.0.{random.randint(1, 255)}",
                    "target_ip": "192.168.1.100",
                    "description": "Attaque SYN Flood détectée",
                    "details": "Plus de 1000 paquets SYN sans ACK",
                    "timestamp": datetime.now().isoformat()
                }
            }

        self.send_message(alert)
        print(f"[AGENT {self.agent_id}] Alerte envoyée: {attack_type}")

    def start(self):
        self.running = True
        self.connect()
        self.register()

        # Threads
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.simulate_traffic, daemon=True).start()

        print(f"[AGENT {self.agent_id}] Démarré. Appuyez sur Ctrl+C pour arrêter.")
        print(f"[AGENT {self.agent_id}] Commandes disponibles:")
        print("  - Envoyer 'scan' pour simuler un port scan")
        print("  - Envoyer 'flood' pour simuler un SYN flood")
        print("  - Envoyer 'quit' pour arrêter")

        try:
            while self.running:
                cmd = input("> ").strip().lower()
                if cmd == "scan":
                    self.simulate_attack("PORT_SCAN")
                elif cmd == "flood":
                    self.simulate_attack("SYN_FLOOD")
                elif cmd == "quit":
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()
        print(f"[AGENT {self.agent_id}] Arrêté")


if __name__ == "__main__":
    import sys

    agent_id = sys.argv[1] if len(sys.argv) > 1 else "agent-test-001"
    agent = TestAgent(agent_id)
    agent.start()