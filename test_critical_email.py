#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NetGuard Pro - Launcher Universel
Démarre : Serveur FastAPI + Collecteur TCP + Agents (optionnel)
Version corrigée avec logging Python standard
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
    GREEN = colorama.Fore.GREEN
    BLUE = colorama.Fore.BLUE
    YELLOW = colorama.Fore.YELLOW
    RED = colorama.Fore.RED
    CYAN = colorama.Fore.CYAN
    RESET = colorama.Style.RESET_ALL
except ImportError:
    GREEN = ""
    BLUE = ""
    YELLOW = ""
    RED = ""
    CYAN = ""
    RESET = ""

# **CRÉER LE RÉPERTOIRE LOGS AVANT DE CONFIGURER LOGGING**
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Configuration logging Python standard - APRÈS création du répertoire
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, f'launcher_{datetime.now().date()}.log')),
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

        # Le répertoire logs existe déjà, pas besoin de le recréer ici

    def log(self, component: str, message: str, color: str = "", log_level: int = logging.INFO):
        """
        Log avec affichage console colorisé ET écriture dans fichier via logging

        Args:
            component: Nom du composant
            message: Message à afficher
            color: Code couleur Colorama
            log_level: Niveau de log (logging.INFO, logging.ERROR, etc.)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Affichage console coloré
        print(f"{color}[{timestamp}] [{component:12}]{RESET} {message}")

        # Écriture dans fichier via logger Python
        logger.log(log_level, f"[{component}] {message}")

    # ... (reste du code identique au précédent)

    def test_email(self):
        """Test complet du système d'email"""
        self.log("TESTER", "🧪 Test système email...", BLUE)

        try:
            from server.services.notifier import test_email
            # **ASYNCIO IMPORTÉ GLOBALEMENT - PAS D'ERREUR**
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

    # ... (reste du code identique au précédent)


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

    # Configuration logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    launcher = NetGuardLauncher()

    # Test configuration uniquement
    if args.config_test:
        print("🔧 Test configuration...")
        health = launcher.get_system_health()
        print(f"Ports API: {'✅' if health['ports']['api'] else '❌'} 8000")
        print(f"Ports Collector: {'✅' if health['ports']['collector'] else '❌'} 9999")
        sys.exit(0)

    try:
        # Démarrage serveur
        if not launcher.start_server():
            print("❌ Échec démarrage serveur")
            sys.exit(1)

        # Démarrage agents automatiques
        for i in range(args.agents):
            launcher.start_agent(f"auto-agent-{i + 1:03d}")

        # Mode interactif ou daemon
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