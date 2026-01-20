from collections import defaultdict, deque
from datetime import datetime, timezone
import scapy.all as scapy


class PortScanDetector:
    def __init__(self, time_window=60, port_threshold=10):
        self.time_window = time_window
        self.port_threshold = port_threshold
        self.scan_data = defaultdict(deque)

    def process_packet(self, packet):
        if not packet.haslayer(scapy.IP) or not packet.haslayer(scapy.TCP):
            return None

        tcp_layer = packet[scapy.TCP]

        # SYN flag (0x02) et PAS ACK (0x10)
        if not (tcp_layer.flags & 0x02):
            return None
        if tcp_layer.flags & 0x10:
            return None

        src_ip = packet[scapy.IP].src
        dst_ip = packet[scapy.IP].dst
        dst_port = tcp_layer.dport

        now = datetime.now(timezone.utc)

        entries = self.scan_data[src_ip]
        entries.append((now, dst_port))

        while entries and (now - entries[0][0]).total_seconds() > self.time_window:
            entries.popleft()

        unique_ports = {p for _, p in entries}

        if len(unique_ports) >= self.port_threshold:
            entries.clear()
            return {
                "alert_type": "PORT_SCAN",
                "severity": "MEDIUM",
                "source_ip": src_ip,
                "target_ip": dst_ip,
                "protocol": "TCP",
                "details": {
                    "ports_scanned": len(unique_ports),
                    "ports": sorted(unique_ports),
                    "time_window": self.time_window,
                    "threshold": self.port_threshold
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return None
