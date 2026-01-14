import scapy.all as scapy


class PacketSniffer:
    def __init__(self, interface="Wi-Fi", packet_callback=None):
        """
        :param interface: interface réseau (ex: 'Wi-Fi' sous Windows)
        :param packet_callback: fonction appelée à chaque paquet
        """
        self.interface = interface
        self.packet_callback = packet_callback
        self.running = False

    def _internal_callback(self, packet):
        """
        Callback interne appelé par Scapy
        """
        try:
            if packet.haslayer(scapy.IP):
                if self.packet_callback:
                    self.packet_callback(packet)
        except Exception as e:
            print(f"[!] Erreur traitement paquet : {e}")

    def start(self):
        """
        Démarrer la capture réseau
        """
        print(f"[+] Démarrage du sniffer sur interface : {self.interface}")
        print("[*] Appuyez sur CTRL+C pour arrêter")

        self.running = True

        try:
            scapy.sniff(
                iface=self.interface,
                prn=self._internal_callback,
                store=False
            )
        except PermissionError:
            print("[!] Permission refusée : lancez le script en administrateur")
        except OSError as e:
            print(f"[!] Erreur interface réseau : {e}")
        except KeyboardInterrupt:
            print("\n[*] Capture arrêtée par l'utilisateur")
        finally:
            self.running = False
            print("[*] Sniffer arrêté")
