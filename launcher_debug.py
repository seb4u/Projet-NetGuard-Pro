#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🎯 DEBUG: Début du fichier launcher.py - Import en cours...")

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

print("✅ DEBUG: Imports standards OK")

# Configuration des couleurs
try:
    import colorama
    print("✅ DEBUG: Colorama importé")
    colorama.init()
    GREEN, BLUE, YELLOW, RED, CYAN, RESET = (
        colorama.Fore.GREEN,
        colorama.Fore.BLUE,
        colorama.Fore.YELLOW,
        colorama.Fore.RED,
        colorama.Fore.CYAN,
        colorama.Style.RESET_ALL
    )
    print("✅ DEBUG: Colorama initialisé")
except ImportError as e:
    print(f"⚠️  DEBUG: Colorama non disponible ({e}) - valeurs par défaut")
    GREEN = BLUE = YELLOW = RED = CYAN = RESET = ""

print("🎯 DEBUG: Configuration logging...")

# **CRÉER LE RÉPERTOIRE LOGS EN PREMIER**
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
print(f"📁 DEBUG: Répertoire logs = {logs_dir}")
os.makedirs(logs_dir, exist_ok=True)
print("✅ DEBUG: Répertoire logs créé/existe")

# Configuration logging
logging.basicConfig(
    level=logging.DEBUG,  # **MODE DEBUG MAXIMUM**
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, f'launcher_{datetime.now().date()}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("launcher")
print("✅ DEBUG: Logger configuré")

logger.debug("🐛 Logger de test - Si vous voyez ça, logging fonctionne !")

# Type alias
ProcessInfo = Tuple[str, subprocess.Popen]
print("✅ DEBUG: Type alias défini")

print("🎯 DEBUG: Définition de la classe NetGuardLauncher...")


class NetGuardLauncher:
    """Orchestrateur principal du système NetGuard Pro"""

    def __init__(self):
        print("🔧 DEBUG: NetGuardLauncher.__init__() appelé")
        self.processes: List[ProcessInfo] = []
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.running = True
        self.start_time = datetime.now()
        print(f"🔧 DEBUG: base_dir = {self.base_dir}")
        logger.debug("Classe NetGuardLauncher initialisée")

    def log(self, component: str, message: str, color: str = "", log_level: int = logging.INFO):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] [{component:12}]{RESET} {message}")
        logger.log(log_level, f"[{component}] {message}")

    # ... (copiez le reste du code ici) ...

    def start_server(self) -> bool:
        """Démarre le serveur FastAPI et le collecteur"""
        self.log("ORCHESTRATOR", "🔍 Vérification des ports...", BLUE)
        logger.debug("Début start_server()")

        for port in [8000, 9999]:
            is_occupied = self.check_port(port)
            logger.debug(f"Port {port} occupé ? {is_occupied}")
            if is_occupied:
                self.log("ORCHESTRATOR", f"Port {port} occupé, libération...", YELLOW)
                self.kill_process_on_port(port)
                time.sleep(2)

        self.log("ORCHESTRATOR", "🚀 Démarrage FastAPI + Collecteur...", BLUE)

        env = os.environ.copy()
        env["PYTHONPATH"] = self.base_dir
        logger.debug(f"PYTHONPATH = {env['PYTHONPATH']}")

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
            logger.debug("Mode Windows détecté (CREATE_NEW_CONSOLE)")

        try:
            logger.debug(f"Exécution : {sys.executable} -m server.main")
            process = subprocess.Popen([sys.executable, "-m", "server.main"], **kwargs)
            self.processes.append(("Server", process))
            logger.debug(f"Processus créé avec PID {process.pid}")

            # Thread de lecture des logs
            def read_output():
                log_file = os.path.join(self.logs_dir, "server_output.log")
                logger.debug(f"Thread read_output() - log_file = {log_file}")
                with open(log_file, 'a') as f:
                    while self.running and process.poll() is None:
                        try:
                            line = process.stdout.readline()
                            if line:
                                f.write(line)
                                if "[FASTAPI]" not in line:
                                    print(f"{BLUE}[FASTAPI]{RESET} {line.strip()}")
                        except Exception as e:
                            logger.exception("Erreur dans thread read_output")

            threading.Thread(target=read_output, daemon=True).start()
            logger.debug("Thread de lecture démarré")

            # Attente avec logs progressifs
            self.log("ORCHESTRATOR", "⏳ Attente démarrage services (max 30s)...", CYAN)
            for i in range(60):
                time.sleep(0.5)

                api_ok = self.check_port(8000)
                collector_ok = self.check_port(9999)

                logger.debug(f"Tentative {i}/60 - API:{api_ok} Collector:{collector_ok}")

                if api_ok and collector_ok:
                    self.log("ORCHESTRATOR", f"✅ API (port 8000) : OK", GREEN)
                    self.log("ORCHESTRATOR", f"✅ Collector (port 9999) : OK", GREEN)
                    time.sleep(1)
                    logger.debug("start_server() terminé avec succès")
                    return True

                if i % 10 == 0 and i > 0:
                    self.log("ORCHESTRATOR", f"  ⏳ En attente... (tentative {i}/60)", YELLOW)

            logger.error("Timeout démarrage services atteint")
            self.log("ORCHESTRATOR", "❌ Timeout démarrage services", RED, logging.ERROR)
            return False

        except Exception as e:
            logger.exception("Erreur fatale dans start_server()")
            self.log("ORCHESTRATOR", f"❌ Erreur démarrage serveur: {e}", RED, logging.ERROR)
            return False

    # ... (copiez TOUT le reste du code ici) ...

    def shutdown(self):
        """Arrêt propre du système complet"""
        print(f"\n{RED}╔═══════════════════════════════════════════════════════╗{RESET}")
        print(f"{RED}║              ARRÊT DU SYSTÈME EN COURS                ║{RESET}")
        print(f"{RED}╚═══════════════════════════════════════════════════════╝{RESET}\n")
        logger.debug("shutdown() appelé")
        # ... (reste du code) ...

print("🎯 DEBUG: Définition de main()...")

def main():
    print("🎯 DEBUG: main() appelé - Parsing arguments...")
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
    print("✅ DEBUG: ArgumentParser créé")

    parser.add_argument("--agents", "-a", type=int, default=0,
                        help="Nombre d'agents à démarrer automatiquement")
    parser.add_argument("--no-interactive", "-n", action="store_true",
                        help="Mode non-interactif (juste le serveur)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Mode verbeux avec logs détaillés")
    parser.add_argument("--config-test", action="store_true",
                        help="Teste la configuration et quitte")

    args = parser.parse_args()
    print(f"✅ DEBUG: Arguments parsés = {args}")

    # Configuration logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        print("✅ DEBUG: Mode verbeux activé")

    launcher = NetGuardLauncher()
    print("✅ DEBUG: Instance NetGuardLauncher créée")

    # Test configuration uniquement
    if args.config_test:
        print("🎯 DEBUG: Mode test config")
        health = launcher.get_system_health()
        print(f"Ports API: {'✅' if health['ports']['api'] else '❌'} 8000")
        print(f"Ports Collector: {'✅' if health['ports']['collector'] else '❌'} 9999")
        sys.exit(0)

    try:
        print("🎯 DEBUG: Début démarrage serveur...")
        # Démarrage serveur
        if not launcher.start_server():
            print("❌ DEBUG: Échec démarrage serveur")
            sys.exit(1)

        print("✅ DEBUG: Serveur démarré")

        # Démarrage agents automatiques
        for i in range(args.agents):
            print(f"🎯 DEBUG: Démarrage agent {i+1}")
            launcher.start_agent(f"auto-agent-{i + 1:03d}")

        # Mode interactif ou daemon
        if not args.no_interactive:
            print("🎯 DEBUG: Mode interactif")
            launcher.interactive_menu()
        else:
            print("🎯 DEBUG: Mode daemon")
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
        print("\n🎯 DEBUG: Ctrl+C détecté")
        launcher.shutdown()
    except Exception as e:
        print(f"❌ DEBUG: Erreur fatale - {e}")
        logger.exception("Erreur fatale")
        launcher.shutdown()


print("🎯 DEBUG: Vérification __main__...")

if __name__ == "__main__":
    print("✅ DEBUG: __name__ == '__main__' - Lancement main()")
    main()
else:
    print(f"⚠️  DEBUG: __name__ = {__name__} - Script importé comme module")