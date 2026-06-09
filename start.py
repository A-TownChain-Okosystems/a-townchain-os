#!/usr/bin/env python3
"""
A-TownChain OS — Start-Skript
Startet alle Dienste in der richtigen Reihenfolge.

Verwendung:
    python3 start.py              # Alle Dienste
    python3 start.py --backend    # Nur Backend
    python3 start.py --gateway    # Nur Gateway
    python3 start.py --bootstrap  # Nur Bootstrap Node

Docker:
    docker-compose up -d
"""
import subprocess, sys, os, time, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, name):
    print(f"  ▶ Starte {name}...")
    return subprocess.Popen(cmd, cwd=ROOT, shell=True)

def main():
    parser = argparse.ArgumentParser(description="A-TownChain OS Launcher")
    parser.add_argument("--backend",   action="store_true", help="Nur Backend starten")
    parser.add_argument("--gateway",   action="store_true", help="Nur Gateway starten")
    parser.add_argument("--bootstrap", action="store_true", help="Nur Bootstrap Node starten")
    parser.add_argument("--all",       action="store_true", help="Alle Dienste starten (default)")
    args = parser.parse_args()

    procs = []
    start_all = not any([args.backend, args.gateway, args.bootstrap])

    if start_all or args.bootstrap:
        procs.append(run("python3 -m blockchain.nodes.bootstrap", "Bootstrap Node :4001"))
        time.sleep(1)

    if start_all or args.backend:
        procs.append(run("python3 backend/main.py", "Backend :5000"))
        time.sleep(1)

    if start_all or args.gateway:
        procs.append(run("python3 gateway/main.py", "Gateway :4000"))

    print(f"\n✅ {len(procs)} Dienst(e) gestartet. Ctrl+C zum Beenden.")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹ Stoppe alle Dienste...")
        for p in procs: p.terminate()

if __name__ == "__main__":
    main()
