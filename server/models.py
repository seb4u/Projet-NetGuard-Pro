from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON
from server.database import Base
from datetime import datetime


class Agent(Base):
    """
    Représente un agent de supervision déployé sur le réseau
    """
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), unique=True, nullable=False, index=True, comment="Identifiant unique de l'agent")
    hostname = Column(String(100), comment="Nom de la machine")
    ip_address = Column(String(45), comment="Adresse IP de l'agent")  # IPv6 compatible
    status = Column(String(20), default="inactive", comment="État: active, inactive, error")
    last_heartbeat = Column(DateTime, default=datetime.now, comment="Dernier signe de vie")
    created_at = Column(DateTime, default=datetime.now, comment="Date d'enregistrement")
    location = Column(String(100), default="Unknown", comment="Emplacement physique")

    def __repr__(self):
        return f"<Agent(id='{self.agent_id}', status='{self.status}')>"


class Alert(Base):
    """
    Alertes de sécurité détectées par les agents
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), comment="Type: PORT_SCAN, SYN_FLOOD, etc.")
    severity = Column(String(20), comment="Niveau: LOW, MEDIUM, HIGH, CRITICAL")
    source_ip = Column(String(45), comment="IP source de l'attaque")
    target_ip = Column(String(45), comment="IP cible")
    description = Column(Text, comment="Description textuelle de l'alerte")
    details = Column(JSON, comment="Données techniques additionnelles (format JSON)")
    timestamp = Column(DateTime, default=datetime.now, comment="Date de détection")
    acknowledged = Column(Boolean, default=False, comment="Accusé de réception")
    acknowledged_by = Column(String(100), comment="Utilisateur ayant acquitté")
    resolved = Column(Boolean, default=False, comment="Problème résolu")
    agent_id = Column(String(50), comment="Agent ayant détecté l'alerte")

    def __repr__(self):
        return f"<Alert(type='{self.alert_type}', severity='{self.severity}')>"


class TrafficData(Base):
    """
    Données de trafic réseau capturées (flux brut)
    """
    __tablename__ = "traffic_data"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), comment="Agent source")
    timestamp = Column(DateTime, default=datetime.now, comment="Horodatage")
    source_ip = Column(String(45), comment="IP source")
    dest_ip = Column(String(45), comment="IP destination")
    protocol = Column(String(20), comment="Protocole: TCP, UDP, ICMP, etc.")
    port = Column(Integer, comment="Port destination")
    packet_size = Column(Integer, comment="Taille du paquet en octets")
    flags = Column(String(20), comment="Flags TCP (SYN, ACK, etc.)")

    def __repr__(self):
        return f"<TrafficData(src='{self.source_ip}', dst='{self.dest_ip}')>"


class Statistics(Base):
    """
    Statistiques agrégées par agent (métriques de performance)
    """
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now, comment="Date de la mesure")
    agent_id = Column(String(50), comment="Agent concerné")
    total_packets = Column(Integer, default=0, comment="Nombre total de paquets traités")
    packets_per_second = Column(Float, default=0.0, comment="Débit paquets/seconde")  # Note: pas 'avg_packets_per_second'
    cpu_usage = Column(Float, default=0.0, comment="Utilisation CPU %")
    memory_usage = Column(Float, default=0.0, comment="Utilisation mémoire %")

    def __repr__(self):
        return f"<Statistics(agent='{self.agent_id}', pps='{self.packets_per_second}')>"