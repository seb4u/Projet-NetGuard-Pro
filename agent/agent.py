from agent.sniffer import PacketSniffer
from agent.detectors.port_scan import PortScanDetector
from agent.detectors.syn_flood import SynFloodDetector

# Détecteurs
port_scan_detector = PortScanDetector(
    time_window=60,
    port_threshold=5
)

syn_flood_detector = SynFloodDetector(
    time_window=10,
    syn_threshold=30
)

def process_packet(packet):
    alert = port_scan_detector.process_packet(packet)
    if alert:
        print("\n🚨 ALERTE PORT SCAN 🚨")
        print(alert)

    alert = syn_flood_detector.process_packet(packet)
    if alert:
        print("\n🔥 ALERTE SYN FLOOD 🔥")
        print(alert)

# Interfaces Windows à surveiller
interfaces = ["Wi-Fi", "Ethernet"]

for iface in interfaces:
    try:
        sniffer = PacketSniffer(
            interface=iface,
            packet_callback=process_packet
        )
        sniffer.start()
    except Exception as e:
        print(f"[!] Interface {iface} ignorée : {e}")
