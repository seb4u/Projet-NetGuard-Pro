from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50), unique=True, nullable=False)
    hostname = Column(String(100))
    ip_address = Column(String(45))
    status = Column(String(20))
    last_heartbeat = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

class TrafficData(Base):
    __tablename__ = 'traffic_data'
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.now)
    source_ip = Column(String(45))
    dest_ip = Column(String(45))
    protocol = Column(String(20))
    port = Column(Integer)
    packet_size = Column(Integer)
    flags = Column(String(20))

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50))
    severity = Column(String(20))
    source_ip = Column(String(45))
    target_ip = Column(String(45))
    description = Column(Text)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)

class Statistics(Base):
    __tablename__ = 'statistics'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    total_packets = Column(Integer)
    total_alerts = Column(Integer)
    active_agents = Column(Integer)
    avg_packets_per_second = Column(Float)
