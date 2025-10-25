import subprocess
import time
import sys
import os
from threading import Thread

def start_api():
    """Démarre le serveur API Flask"""
    try:
        api_process = subprocess.Popen(
            [sys.executable, "api.py"],
            stdout=open('api.log', 'w'),
            stderr=subprocess.STDOUT,
            env=os.environ
        )
        print(f"✅ Serveur API démarré (PID: {api_process.pid})")
        return api_process
    except Exception as e:
        print(f"❌ Erreur démarrage API: {e}")
        sys.exit(1)

def start_dashboard():
    """Démarre le tableau de bord Dash"""
    try:
        # Attendre que l'API soit disponible
        while True:
            try:
                if os.system(f"netcast -ano | findstr :{port}>nul") == 0:
                    break
            except:
                pass
            time.sleep(1)
       
        dash_process = subprocess.Popen(
            [sys.executable, "TabdeBord.py"],
            stdout=open('dashboard.log', 'w'),
            stderr=subprocess.STDOUT,
            env=os.environ
        )
        print(f"✅ Tableau de bord démarré (PID: {dash_process.pid})")
        return dash_process
    except Exception as e:
        print(f"❌ Erreur démarrage Dashboard: {e}")
        sys.exit(1)

def monitor_processes(api_proc, dash_proc):
    """Surveille les processus et redémarre si nécessaire"""
    while True:
        if api_proc.poll() is not None:
            print("⚠️ Serveur API arrêté, redémarrage...")
            api_proc = start_api()
       
        if dash_proc.poll() is not None:
            print("⚠️ Tableau de bord arrêté, redémarrage...")
            dash_proc = start_dashboard()
       
        time.sleep(5)

if __name__ == "__main__":
    print("🚀 Démarrage du système de monitoring...")
   
    # Démarrer les processus
    api_process = start_api()
    dash_process = start_dashboard()
   
    # Lancer le monitoring
    try:
        monitor_thread = Thread(target=monitor_processes, args=(api_process, dash_process))
        monitor_thread.daemon = True
        monitor_thread.start()
       
        print("\nSystème opérationnel :")
        print(f"• API:      http://localhost:5000")
        print(f"• Dashboard: http://localhost:8050")
        print("\nCTRL+C pour arrêter")
       
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt des processus...")
        api_process.terminate()
        dash_process.terminate()
        sys.exit(0)
