from collections import defaultdict, deque
from datetime import datetime, timezone
import scapy.all as scapy


class SynFloodDetector:
    def __init__(self, time_window=10, syn_threshold=10):
        """
        :param time_window: fenêtre temporelle en secondes
        :param syn_threshold: nombre de SYN déclenchant l’alerte
        """
        self.time_window = time_window
        self.syn_threshold = syn_threshold

        # { target_ip: deque[timestamps] }
        self.syn_packets = defaultdict(deque)

    def process_packet(self, packet):
        if not packet.haslayer(scapy.IP) or not packet.haslayer(scapy.TCP):
            return None

        tcp_layer = packet[scapy.TCP]

        # SYN flag (0x02) uniquement
        if not (tcp_layer.flags & 0x02):
            return None

        src_ip = packet[scapy.IP].src
        dst_ip = packet[scapy.IP].dst

        now = datetime.now(timezone.utc)
        entries = self.syn_packets[dst_ip]
        entries.append(now)

        # Nettoyage fenêtre temporelle
        while entries and (now - entries[0]).total_seconds() > self.time_window:
            entries.popleft()

        if len(entries) >= self.syn_threshold:
            entries.clear()  # éviter spam
            return {
                "alert_type": "SYN_FLOOD",
                "severity": "HIGH",
                "source_ip": src_ip,
                "target_ip": dst_ip,
                "protocol": "TCP",
                "details": {
                    "syn_count": self.syn_threshold,
                    "time_window": self.time_window
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return None
