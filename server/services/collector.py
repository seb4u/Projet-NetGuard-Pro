import socket
import threading
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import time
from contextlib import contextmanager

from server.database import SessionLocal
from server.models import Agent, Alert, TrafficData, Statistics
from server.services.notifier import get_notifier

# Logger dédié pour le collecteur
logger = logging.getLogger("collector")

# Schema de validation des messages
MESSAGE_SCHEMA = {
    "REGISTER": ["agent_id", "hostname"],
    "HEARTBEAT": ["agent_id"],
    "ALERT": ["agent_id", "alert"],
    "TRAFFIC_DATA": ["agent_id", "data"],
    "STATISTICS": ["agent_id", "data"]
}


class CollectorServer:
    """Serveur de collecte TCP multi-agents avec validation et monitoring"""

    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.agents: Dict[str, dict] = {}
        self.running = False
        self.server_socket = None
        self.stats = {
            "messages_processed": 0,
            "alerts_received": 0,
            "errors": 0,
            "start_time": None
        }
        self._cleanup_thread = None
        self._notifier = get_notifier()

    def start(self):
        """Démarre le serveur de collecte avec thread de nettoyage"""
        self.running = True
        self.stats["start_time"] = datetime.now()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.settimeout(1.0)  # Timeout pour permettre vérification running
        self.server_socket.listen(5)

        logger.info(f"[COLLECTOR] Serveur démarré sur {self.host}:{self.port}")

        # Thread de nettoyage automatique
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_inactive_agents,
            daemon=True
        )
        self._cleanup_thread.start()

        # Boucle principale d'acceptation
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(60.0)  # Timeout lecture
                logger.info(f"[COLLECTOR] Nouvelle connexion: {address}")

                thread = threading.Thread(
                    target=self.handle_agent,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"[COLLECTOR] Erreur accept: {e}")

    def _cleanup_inactive_agents(self):
        """Nettoie périodiquement les agents inactifs (>5min)"""
        while self.running:
            try:
                time.sleep(60)  # Vérification toutes les minutes
                now = datetime.now()
                inactive_agents = []

                for agent_id, agent_data in list(self.agents.items()):
                    if now - agent_data['last_seen'] > timedelta(minutes=5):
                        inactive_agents.append(agent_id)

                for agent_id in inactive_agents:
                    self._deactivate_agent(agent_id)

            except Exception as e:
                logger.error(f"[COLLECTOR] Erreur nettoyage: {e}")

    def _deactivate_agent(self, agent_id: str):
        """Désactive un agent en DB et le retire du dict"""
        try:
            with self._get_db() as db:
                agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
                if agent:
                    agent.status = 'inactive'
                    db.commit()
                    logger.warning(f"[COLLECTOR] Agent {agent_id} marqué comme inactif")

            if agent_id in self.agents:
                del self.agents[agent_id]
        except Exception as e:
            logger.error(f"[COLLECTOR] Erreur désactivation agent {agent_id}: {e}")

    @contextmanager
    def _get_db(self):
        """Context manager pour les sessions DB"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _validate_message(self, message: Dict[str, Any], msg_type: str) -> bool:
        """Valide le message selon le schema"""
        if msg_type not in MESSAGE_SCHEMA:
            logger.error(f"Type de message inconnu: {msg_type}")
            return False

        required = MESSAGE_SCHEMA[msg_type]
        missing = [field for field in required if field not in message]

        if missing:
            logger.error(f"Champs manquants pour {msg_type}: {missing}")
            return False

        return True

    def handle_agent(self, client_socket: socket.socket, address: tuple):
        """Gère la communication avec un agent avec validation robuste"""
        agent_id = None
        buffer = ""

        try:
            while self.running:
                try:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break

                    buffer += data
                    messages = buffer.split('\n')
                    buffer = messages.pop()  # Dernier message incomplet

                    for msg_str in messages:
                        if not msg_str.strip():
                            continue

                        try:
                            message = json.loads(msg_str)
                            msg_type = message.get('type')
                            agent_id = message.get('agent_id', 'unknown')

                            # Validation du message
                            if not self._validate_message(message, msg_type):
                                continue

                            self._process_message(msg_type, message, agent_id, address)
                            self.stats["messages_processed"] += 1

                        except json.JSONDecodeError as e:
                            logger.error(f"[COLLECTOR] JSON invalide de {address}: {e}")
                            self.stats["errors"] += 1
                        except Exception as e:
                            logger.error(f"[COLLECTOR] Erreur traitement message: {e}")
                            self.stats["errors"] += 1

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"[COLLECTOR] Erreur réception données {address}: {e}")
                    break

        except Exception as e:
            logger.error(f"[COLLECTOR] Erreur connexion {address}: {e}")
        finally:
            if agent_id and agent_id != 'unknown':
                self._deactivate_agent(agent_id)

            try:
                client_socket.close()
                logger.info(f"[COLLECTOR] Connexion fermée: {address}")
            except:
                pass

    def _process_message(self, msg_type: str, message: Dict[str, Any], agent_id: str, address: tuple):
        """Traite un message validé"""
        with self._get_db() as db:
            try:
                if msg_type == 'REGISTER':
                    self._handle_register(message, agent_id, address, db)
                elif msg_type == 'HEARTBEAT':
                    self._handle_heartbeat(agent_id, db)
                elif msg_type == 'ALERT':
                    self._handle_alert(message, agent_id, db)
                elif msg_type == 'TRAFFIC_DATA':
                    self._handle_traffic(message, agent_id, db)
                elif msg_type == 'STATISTICS':
                    self._handle_statistics(message, agent_id, db)

            except Exception as e:
                logger.error(f"[COLLECTOR] Erreur processing {msg_type} from {agent_id}: {e}")
                self.stats["errors"] += 1

    def _handle_register(self, message: Dict[str, Any], agent_id: str, address: tuple, db):
        """Gère l'enregistrement d'un agent"""
        self.agents[agent_id] = {
            'socket': None,  # Non stocké pour éviter pickling issues
            'address': address,
            'last_seen': datetime.now()
        }

        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            agent = Agent(
                agent_id=agent_id,
                hostname=message.get('hostname', 'Unknown'),
                ip_address=address[0],
                status='active',
                location=message.get('location', 'Unknown')
            )
            db.add(agent)
            logger.info(f"[COLLECTOR] Nouvel agent {agent_id} enregistré")
        else:
            agent.status = 'active'
            agent.hostname = message.get('hostname', agent.hostname)
            agent.ip_address = address[0]
            agent.last_heartbeat = datetime.now()
            logger.info(f"[COLLECTOR] Agent {agent_id} rejoint")

        db.commit()

    def _handle_heartbeat(self, agent_id: str, db):
        """Gère le heartbeat d'un agent"""
        if agent_id in self.agents:
            self.agents[agent_id]['last_seen'] = datetime.now()

        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            agent.last_heartbeat = datetime.now()
            agent.status = 'active'
            db.commit()

    def _handle_alert(self, message: Dict[str, Any], agent_id: str, db):
        """Gère une alerte de sécurité"""
        alert_data = message.get('alert', {})

        alert = Alert(
            alert_type=alert_data.get('type', 'UNKNOWN'),
            severity=alert_data.get('severity', 'MEDIUM'),
            source_ip=alert_data.get('source_ip'),
            target_ip=alert_data.get('target_ip'),
            description=alert_data.get('description'),
            details=alert_data,
            agent_id=agent_id
        )
        db.add(alert)
        db.commit()

        self.stats["alerts_received"] += 1
        logger.warning(f"[ALERT] {alert_data.get('type')} ({alert_data.get('severity')}) from {agent_id}")

        # Notification email si critique/haute
        if alert_data.get('severity') in ['CRITICAL', 'HIGH']:
            try:
                # Enrichir les données pour email
                email_data = alert_data.copy()
                email_data['agent_id'] = agent_id
                email_data['timestamp'] = alert_data.get('timestamp', datetime.now().isoformat())

                asyncio.run(self._notifier.send_alert(email_data))
                logger.info(f"[ALERT] Email notification envoyé pour {alert.id}")
            except Exception as e:
                logger.error(f"[ALERT] Erreur envoi email: {e}")

    def _handle_traffic(self, message: Dict[str, Any], agent_id: str, db):
        """Gère les données de trafic"""
        traffic = message.get('data', {})

        traffic_entry = TrafficData(
            agent_id=agent_id,
            source_ip=traffic.get('source_ip'),
            dest_ip=traffic.get('dest_ip'),
            protocol=traffic.get('protocol'),
            port=traffic.get('port'),
            packet_size=traffic.get('packet_size'),
            flags=traffic.get('flags')
        )
        db.add(traffic_entry)
        db.commit()

        logger.debug(f"[TRAFFIC] Données reçues de {agent_id}")

    def _handle_statistics(self, message: Dict[str, Any], agent_id: str, db):
        """Gère les statistiques de performance"""
        stats = message.get('data', {})

        stat_entry = Statistics(
            agent_id=agent_id,
            total_packets=stats.get('total_packets', 0),
            packets_per_second=stats.get('packets_per_second', 0.0),
            cpu_usage=stats.get('cpu_usage', 0.0),
            memory_usage=stats.get('memory_usage', 0.0)
        )
        db.add(stat_entry)
        db.commit()

        logger.debug(f"[STATS] Stats reçues de {agent_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du collecteur"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "agents_connected": len(self.agents),
            "messages_processed": self.stats["messages_processed"],
            "alerts_received": self.stats["alerts_received"],
            "errors": self.stats["errors"]
        }

    def stop(self):
        """Arrêt propre du collecteur"""
        logger.info("[COLLECTOR] Arrêt en cours...")
        self.running = False

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # Désactiver tous les agents
        for agent_id in list(self.agents.keys()):
            self._deactivate_agent(agent_id)

        logger.info("[COLLECTOR] Serveur arrêté")


# Instance singleton
_collector_instance = None


def get_collector() -> CollectorServer:
    """Factory pour obtenir l'instance singleton du collecteur"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = CollectorServer()
    return _collector_instance