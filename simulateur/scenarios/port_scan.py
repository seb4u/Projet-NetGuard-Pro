from scapy.all import IP, TCP, send
import random
import time


def simulate_port_scan(
    target_ip,
    ports=None,
    packet_delay=0.05
):
    """
    Simule un port scan TCP SYN
    :param target_ip: IP de la machine cible
    :param ports: liste de ports à scanner
    :param packet_delay: délai entre les paquets (secondes)
    """

    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 139, 443, 445]

    print("[SIMULATEUR] Démarrage simulation PORT SCAN")
    print(f"[SIMULATEUR] Cible : {target_ip}")
    print(f"[SIMULATEUR] Ports : {ports}")

    source_ip = f"192.168.1.{random.randint(10, 250)}"

    for port in ports:
        pkt = IP(
            src=source_ip,
            dst=target_ip
        ) / TCP(
            sport=random.randint(1024, 65535),
            dport=port,
            flags="S"
        )

        send(pkt, verbose=False)
        time.sleep(packet_delay)

    print("[SIMULATEUR] Simulation PORT SCAN terminée")


if __name__ == "__main__":
    # ⚠️ METS ICI L’IP DE TA MACHINE (Wi-Fi)
    TARGET_IP = "10.5.2.1"

    simulate_port_scan(TARGET_IP)
