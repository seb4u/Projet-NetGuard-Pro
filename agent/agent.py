from client import SocketClient
from datetime import datetime, timezone
from sniffer import PacketSniffer

client = SocketClient(
    server_host="localhost",
    server_port=9999,
    agent_id="agent-001"
)

client.connect()
client.register()


alert = {
    "alert_type": "PORT_SCAN",
    "severity": "MEDIUM",
    "source_ip": "10.5.2.184",
    "target_ip": "8.8.8.8",
    "protocol": "TCP",
    "details": {
        "ports_scanned": 443,
        "time_window": 60
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}
client.send_alert(alert)


def process_packet(packet):
    print(packet.summary())

sniffer = PacketSniffer(
    interface="Wi-Fi",
    packet_callback=process_packet
)

sniffer.start()