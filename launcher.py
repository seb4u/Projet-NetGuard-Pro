#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetGuard Pro - Launcher Universel
VERSION FINALE - Toutes les méthodes dans la classe, logs_dir défini
"""

import subprocess
import sys
import time
import os
import signal
import socket
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import threading
import argparse
import logging
import asyncio

# Configuration des couleurs
try:
    import colorama

    colorama.init()
    GREEN, BLUE, YELLOW, RED, CYAN, RESET = (
        colorama.Fore.GREEN,
        colorama.Fore.BLUE,
        colorama.Fore.YELLOW,
        colorama.Fore.RED,
        colorama.Fore.CYAN,
        colorama.Style.RESET_ALL
    )
except ImportError:
    GREEN = BLUE = YELLOW = RED = CYAN = RESET = ""

# CRÉER LE RÉPERTOIRE LOGS GLOBAL (pour le FileHandler)
logs_dir_global = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir_global, exist_ok=True)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir_global, f'launcher_{datetime.now().date()}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("launcher")

# Type alias
ProcessInfo = Tuple[str, subprocess.Popen]


class NetGuardLauncher:
    """Orchestrateur principal du système NetGuard Pro"""

    def __init__(self):
        self.processes: List[ProcessInfo] = []
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.running = True
        self.start_time = datetime.now()

        # ** CRUCIAL : Définir logs_dir comme attribut d'instance **
        self.logs_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)

    def log(self, component: str, message: str, color: str = "", log_level: int = logging.INFO):
        """Log avec affichage console colorisé ET écriture dans fichier"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{component:12}]{RESET} {message}")
        logger.log(log_level, f"[{component}] {message}")

    def check_port(self, port: int, host: str = 'localhost') -> bool:
        """Vérifie si un port est OCCUPÉ (serveur en écoute)"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex((host, port)) == 0
        except Exception as e:
            logger.error(f"Erreur vérification port {port}: {e}")
            return False

    def kill_process_on_port(self, port: int) -> bool:
        """Tue le processus utilisant un port"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            self.log("SYSTEM", f"Libération du port {port} (PID: {pid})", YELLOW)
                            subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                            time.sleep(1)
                            return True
            else:
                result = subprocess.run(['lsof', '-ti', f'tcp:{port}'], capture_output=True, text=True)
                if result.stdout.strip():
                    pid = result.stdout.strip().split('\n')[0]
                    self.log("SYSTEM", f"Libération du port {port} (PID: {pid})", YELLOW)
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    return True
        except Exception as e:
            logger.error(f"Erreur liberation port {port}: {e}")
        return False

    def start_server(self) -> bool:
        """Démarre le serveur FastAPI et le collecteur"""
        self.log("ORCHESTRATOR", "🔍 Vérification des ports...", BLUE)

        for port in [8000, 9999]:
            if self.check_port(port):
                self.log("ORCHESTRATOR", f"Port {port} occupé, libération...", YELLOW)
                self.kill_process_on_port(port)
                time.sleep(2)

        self.log("ORCHESTRATOR", "🚀 Démarrage FastAPI + Collecteur...", BLUE)

        env = os.environ.copy()
        env["PYTHONPATH"] = self.base_dir

        kwargs = {
            'cwd': self.base_dir,
            'env': env,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'bufsize': 1,
            'universal_newlines': True
        }

        if sys.platform == "win32":
            kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE

        try:
            process = subprocess.Popen([sys.executable, "-m", "server.main"], **kwargs)
            self.processes.append(("Server", process))

            def read_output():
                log_file = os.path.join(self.logs_dir, "server_output.log")
                with open(log_file, 'a') as f:
                    while self.running and process.poll() is None:
                        try:
                            line = process.stdout.readline()
                            if line:
                                f.write(line)
                                if "[FASTAPI]" not in line:
                                    print(f"{BLUE}[FASTAPI]{RESET} {line.strip()}")
                        except:
                            break

            threading.Thread(target=read_output, daemon=True).start()

            # Attente avec logs progressifs
            self.log("ORCHESTRATOR", "⏳ Attente démarrage services (max 30s)...", CYAN)
            for i in range(60):
                time.sleep(0.5)

                api_ok = self.check_port(8000)
                collector_ok = self.check_port(9999)

                if api_ok and collector_ok:
                    self.log("ORCHESTRATOR", f"✅ API (port 8000) : OK", GREEN)
                    self.log("ORCHESTRATOR", f"✅ Collector (port 9999) : OK", GREEN)
                    time.sleep(1)
                    return True

                if i % 10 == 0 and i > 0:
                    self.log("ORCHESTRATOR", f"  ⏳ En attente... (tentative {i}/60)", YELLOW)

            self.log("ORCHESTRATOR", "❌ Timeout démarrage services", RED, logging.ERROR)
            return False

        except Exception as e:
            logger.exception("Erreur fatale dans start_server()")
            self.log("ORCHESTRATOR", f"❌ Erreur démarrage serveur: {e}", RED, logging.ERROR)
            return False

    def start_agent(self, agent_id: str) -> bool:
        """Démarre un agent de test"""
        self.log("AGENT", f"Démarrage {agent_id}...", YELLOW)

        env = os.environ.copy()
        env["PYTHONPATH"] = self.base_dir

        kwargs = {
            'cwd': self.base_dir,
            'env': env,
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'bufsize': 1
        }

        if sys.platform == "win32":
            kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE

        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "agent.agent", agent_id],
                **kwargs
            )
            self.processes.append((f"Agent-{agent_id}", process))
            time.sleep(1)
            self.log("AGENT", f"✅ Agent {agent_id} démarré", GREEN)
            return True
        except Exception as e:
            self.log("AGENT", f"❌ Erreur démarrage agent {agent_id}: {e}", RED, logging.ERROR)
            return False

    def simulate_attack(self, attack_type: str):
        """Envoie une alerte de test au serveur"""
        self.log("SIMULATOR", f"Simulation {attack_type}...", YELLOW)

        try:
            import json

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(('localhost', 9999))

                register_msg = json.dumps({
                    "type": "REGISTER",
                    "agent_id": "simulator",
                    "hostname": "simulation-console"
                })
                s.send(register_msg.encode() + b'\n')
                s.recv(1024)

                alert_data = {
                    "type": "ALERT",
                    "agent_id": "simulator",
                    "alert": {
                        "type": attack_type,
                        "severity": "CRITICAL" if attack_type == "SYN_FLOOD" else "HIGH",
                        "source_ip": f"203.0.113.{hash(attack_type) % 255}",
                        "target_ip": "192.168.1.100",
                        "description": f"Simulation {attack_type} depuis le launcher",
                        "timestamp": datetime.now().isoformat(),
                        "details": {"simulated": True, "tool": "launcher.py"}
                    }
                }

                s.send(json.dumps(alert_data).encode() + b'\n')

            self.log("SIMULATOR", f"✅ Alerte {attack_type} envoyée!", GREEN)
            return True

        except Exception as e:
            self.log("SIMULATOR", f"❌ Erreur simulation: {e}", RED, logging.ERROR)
            return False

    def test_email(self):
        """Test complet du système d'email"""
        self.log("TESTER", "🧪 Test système email...", BLUE)

        try:
            from server.services.notifier import test_email
            success = asyncio.run(test_email())

            if success:
                self.log("TESTER", "✅ Système email opérationnel", GREEN)
            else:
                self.log("TESTER", "❌ Système email - Vérifier logs", RED, logging.ERROR)

            return success

        except Exception as e:
            self.log("TESTER", f"❌ Erreur test email: {e}", RED, logging.ERROR)
            logger.exception("Erreur test_email")
            return False

    def show_status(self):
        """Affiche le statut détaillé des services"""
        print(f"\n{CYAN}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{CYAN}║         NETGUARD PRO - STATUT DES SERVICES            ║{RESET}")
        print(f"{CYAN}╚═══════════════════════════════════════════════════════╝{RESET}\n")

        uptime = datetime.now() - self.start_time

        for name, process in self.processes:
            status = f"{GREEN}● EN COURS{RESET}" if process.poll() is None else f"{RED}● ARRÊTÉ{RESET}"
            pid = process.pid
            print(f"  {name:20} PID:{pid:6}  {status}")

        print()

        ports_status = []
        for port, name in [(8000, "API"), (9999, "Collector")]:
            open_status = self.check_port(port)
            status_str = f"{GREEN}OUVERT{RESET}" if open_status else f"{RED}FERMÉ{RESET}"
            ports_status.append((name, port, status_str))

        for name, port, status in ports_status:
            print(f"  Port {name} ({port:4}) : {status}")

        print()

        print(f"  💻 Uptime: {str(uptime).split('.')[0]}")
        print(f"  📊 Agents gérés: {sum(1 for p in self.processes if 'Agent' in p[0])}")

        print(f"\n{CYAN}═══════════════════════════════════════════════════════{RESET}\n")

    def stop_all_agents(self):
        """Arrête tous les agents"""
        self.log("STOPPER", "Arrêt des agents...", YELLOW)

        agents = [(name, p) for name, p in self.processes if 'Agent' in name]
        for name, process in agents:
            self.log("STOPPER", f"Arrêt {name}...", YELLOW)
            try:
                if sys.platform == "win32":
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
            except:
                pass

        time.sleep(2)
        self.processes = [(n, p) for n, p in self.processes if 'Agent' not in n]
        self.log("STOPPER", "✅ Agents arrêtés", GREEN)
        return True

    def restart_server(self):
        """Redémarre le serveur principal"""
        self.log("RESTART", "Redémarrage serveur...", YELLOW)

        server_processes = [(n, p) for n, p in self.processes if n == "Server"]
        for name, process in server_processes:
            try:
                process.terminate()
                time.sleep(2)
            except:
                pass

        return self.start_server()

    def shutdown(self):
        """Arrêt propre du système complet"""
        print(f"\n{RED}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║              ARRÊT DU SYSTÈME EN COURS                ║{RESET}")
        print(f"{RED}╚═══════════════════════════════════════════════════════╝{RESET}\n")

        self.running = False

        for name, process in self.processes:
            self.log("SHUTDOWN", f"Arrêt de {name}...", RED)
            try:
                if sys.platform == "win32":
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                else:
                    process.send_signal(signal.SIGTERM)
                    process.wait(timeout=5)
            except Exception as e:
                logger.exception(f"Erreur arrêt {name}")

        self.log("SYSTEM", "✅ Tous les services arrêtés", GREEN)
        sys.exit(0)

    def get_system_health(self) -> Dict[str, Any]:
        """Retourne l'état de santé du système"""
        return {
            "running": self.running,
            "uptime": str(datetime.now() - self.start_time),
            "processes": len(self.processes),
            "ports": {
                "api": self.check_port(8000),
                "collector": self.check_port(9999)
            }
        }

    def interactive_menu(self):
        """Menu interactif pour contrôler le système"""
        print(f"\n{GREEN}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{GREEN}║           NETGUARD PRO - MENU PRINCIPAL               ║{RESET}")
        print(f"{GREEN}╚═══════════════════════════════════════════════════════╝{RESET}\n")

        commands = {
            "1": ("Lancer un agent supplémentaire", self._cmd_start_agent),
            "2": ("Simuler une attaque PORT_SCAN", lambda: self.simulate_attack("PORT_SCAN")),
            "3": ("Simuler une attaque SYN_FLOOD", lambda: self.simulate_attack("SYN_FLOOD")),
            "4": ("Vérifier l'état des services", self.show_status),
            "5": ("Tester l'envoi d'email", self.test_email),
            "6": ("Arrêter tous les agents", self.stop_all_agents),
            "7": ("Redémarrer le serveur", self.restart_server),
            "Q": ("Quitter proprement", self.shutdown),
        }

        for key, (desc, _) in commands.items():
            print(f"  [{key}] {desc}")

        print(f"\n{CYAN}───────────────────────────────────────────────────────{RESET}\n")

        while self.running:
            try:
                cmd = input(f"{GREEN}NetGuard-Pro → {RESET}").strip().upper()

                if cmd in commands:
                    action = commands[cmd][1]
                    try:
                        success = action()
                        if success is False:
                            self.log("ERROR", "Commande échouée", RED, logging.ERROR)
                    except Exception as e:
                        self.log("ERROR", f"Erreur commande: {e}", RED, logging.ERROR)
                else:
                    print(f"{YELLOW}Commande inconnue. Choisissez 1-7 ou Q{RESET}")

            except KeyboardInterrupt:
                self.log("SYSTEM", "Ctrl+C détecté", YELLOW, logging.WARNING)
                confirm = input("Voulez-vous vraiment quitter? (O/N): ").strip().lower()
                if confirm == 'o':
                    break
            except Exception as e:
                self.log("ERROR", f"Erreur inattendue: {e}", RED, logging.ERROR)

        self.shutdown()

    def _cmd_start_agent(self):
        """Handler pour commande démarrage agent"""
        agent_id = input("Nom de l'agent (ex: agent-002): ").strip()
        if agent_id:
            return self.start_agent(agent_id)
        return False


def main():
    """Point d'entrée principal avec argparse"""
    parser = argparse.ArgumentParser(
        description="NetGuard Pro Launcher - Système de Détection d'Intrusions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes d'utilisation:
  # Mode interactif (par défaut)
  python launcher.py

  # Mode daemon avec 3 agents
  python launcher.py --agents 3 --no-interactive

  # Mode debug avec logs détaillés
  python launcher.py -v
        """
    )

    parser.add_argument("--agents", "-a", type=int, default=0,
                        help="Nombre d'agents à démarrer automatiquement")
    parser.add_argument("--no-interactive", "-n", action="store_true",
                        help="Mode non-interactif (juste le serveur)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Mode verbeux avec logs détaillés")
    parser.add_argument("--config-test", action="store_true",
                        help="Teste la configuration et quitte")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    launcher = NetGuardLauncher()

    if args.config_test:
        print("🔧 Test configuration...")
        health = launcher.get_system_health()
        print(f"Ports API: {'✅' if health['ports']['api'] else '❌'} 8000")
        print(f"Ports Collector: {'✅' if health['ports']['collector'] else '❌'} 9999")
        sys.exit(0)

    try:
        if not launcher.start_server():
            print("❌ Échec démarrage serveur")
            sys.exit(1)

        for i in range(args.agents):
            launcher.start_agent(f"auto-agent-{i + 1:03d}")

        if not args.no_interactive:
            launcher.interactive_menu()
        else:
            print(f"\n{GREEN}╔═══════════════════════════════════════════════════════╗{RESET}")
            print(f"{GREEN}║              MODE DAEMON ACTIVÉ                       ║{RESET}")
            print(f"{GREEN}║  Serveur en cours d'exécution (Ctrl+C pour arrêter) ║{RESET}")
            print(f"{GREEN}╚═══════════════════════════════════════════════════════╝{RESET}\n")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                launcher.shutdown()

    except KeyboardInterrupt:
        launcher.shutdown()
    except Exception as e:
        logger.exception("Erreur fatale")
        launcher.shutdown()


if __name__ == "__main__":
    main()