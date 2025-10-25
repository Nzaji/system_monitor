import psutil
import mysql.connector
import pandas as pd
import time
import wmi
import win32evtlog
from datetime import datetime
import sys
import ctypes
import logging

# Configuration du logging
logging.basicConfig(filename='system_monitor.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Redémarrage en mode administrateur si nécessaire
def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    params = " ".join([f'"{arg}"' for arg in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

run_as_admin()

# Configuration MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",  # Remplir avec le mot de passe
    "database": "system_prediction"
}

def setup_database():
    try:
        conn = mysql.connector.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS system_prediction")
        conn.close()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Table métriques système
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            cpu_usage FLOAT,
            ram_usage FLOAT,
            disk_usage FLOAT,
            network_sent BIGINT,
            network_received BIGINT,
            network_packets_lost FLOAT,  # Taux de paquets perdus
            bandwidth_usage FLOAT,       # Bande passante utilisée
            memory_error_rate FLOAT,     # Taux d'erreur de mémoire
            motherboard_temp FLOAT,
            cpu_usage_ma FLOAT,         # Moyenne mobile de l'utilisation du CPU
            disk_errors_diff INT         # Taux de changement des erreurs de disque
        )
        """)

        # Table données SMART
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS smart_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            disk_model VARCHAR(255),
            serial_number VARCHAR(255),
            temperature FLOAT,
            power_on_hours INT,
            reallocated_sectors INT,
            read_errors INT,            # Taux d'erreur de lecture
            write_errors INT,           # Taux d'erreur d'écriture
            disk_status VARCHAR(50)
        )
        """)

        # Table logs système, application et sécurité
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS event_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            log_type VARCHAR(50),
            event_id INT,
            source VARCHAR(255),
            level VARCHAR(50),
            message TEXT
        )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de la configuration de la base de données : {e}")

# Capture des métriques système
def get_system_metrics():
    try:
        c = wmi.WMI()
        motherboard_temp = None
        try:
            sensors = c.MSAcpi_ThermalZoneTemperature()
            if sensors:
                motherboard_temp = (sensors[0].CurrentTemperature / 10.0) - 273.15
        except Exception:
            motherboard_temp = 0

        # Capture des métriques réseau
        net_io = psutil.net_io_counters()
        packets_sent = net_io.packets_sent
        packets_recv = net_io.packets_recv
        packets_lost = 0  # À remplacer par une méthode pour capturer les paquets perdus
        bandwidth_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # En MB

        # Capture du taux d'erreur de mémoire
        memory_error_rate = 0  # À remplacer par une méthode pour capturer les erreurs de mémoire

        return {
            "timestamp": datetime.now(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "ram_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_sent": net_io.bytes_sent,
            "network_received": net_io.bytes_recv,
            "network_packets_lost": packets_lost,
            "bandwidth_usage": bandwidth_usage,
            "memory_error_rate": memory_error_rate,
            "motherboard_temp": motherboard_temp
        }
    except Exception as e:
        logging.error(f"Erreur lors de la collecte des métriques système : {e}")
        return None

# Capture des données SMART
def get_smart_data():
    try:
        smart = wmi.WMI(namespace="root\\wmi")
        disks = smart.MSStorageDriver_FailurePredictStatus()
        disk_info = []
        for disk in disks:
            status = "OK" if not disk.PredictFailure else "Failing"
            model = disk.InstanceName

            # Récupérer les données supplémentaires SMART
            smart_data = smart.MSStorageDriver_ATAPISmartData()
            power_on_hours = 0
            reallocated_sectors = 0
            read_errors = 0
            write_errors = 0
            for data in smart_data:
                if model in data.InstanceName:
                    power_on_hours = int.from_bytes(data.VendorSpecific[192:194], byteorder='little')
                    reallocated_sectors = int.from_bytes(data.VendorSpecific[196:198], byteorder='little')
                    read_errors = int.from_bytes(data.VendorSpecific[200:202], byteorder='little')
                    write_errors = int.from_bytes(data.VendorSpecific[204:206], byteorder='little')

            temp = None
            if smart.MSStorageDriver_ATAPISmartData():
                temp = smart.MSStorageDriver_ATAPISmartData()[0].VendorSpecific[194]

            disk_info.append({
                "timestamp": datetime.now(),
                "disk_model": model,
                "serial_number": "Unknown",
                "temperature": temp if temp else 0,
                "power_on_hours": power_on_hours,
                "reallocated_sectors": reallocated_sectors,
                "read_errors": read_errors,
                "write_errors": write_errors,
                "disk_status": status
            })
        return disk_info
    except Exception as e:
        logging.error(f"Erreur lors de la collecte des données SMART : {e}")
        return []

# Capture des logs système, application et sécurité
def get_windows_logs(log_types=["System", "Application", "Security"], max_events=5):
    logs = []
    for log_type in log_types:
        try:
            hand = win32evtlog.OpenEventLog(None, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(hand, flags, 0, max_events)
            for event in events:
                message = event.StringInserts if event.StringInserts else "No message"
                level = "Information"
                if event.EventType == 1:
                    level = "Error"
                elif event.EventType == 2:
                    level = "Warning"

                logs.append({
                    "timestamp": datetime.now(),
                    "log_type": log_type,
                    "event_id": event.EventID,
                    "source": event.SourceName,
                    "level": level,
                    "message": " ".join(message) if isinstance(message, (list, tuple)) else message
                })
        except Exception as e:
            logging.error(f"Erreur lors de la collecte des logs {log_type} : {e}")
    return logs

# Insertion des métriques dans la table métriques
def insert_metrics(metrics):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO system_metrics (timestamp, cpu_usage, ram_usage, disk_usage, network_sent, network_received, motherboard_temp)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            metrics["timestamp"], metrics["cpu_usage"], metrics["ram_usage"], metrics["disk_usage"],
            metrics["network_sent"], metrics["network_received"], metrics["motherboard_temp"]
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de l'insertion des métriques : {e}")

# Insertion des données SMART dans la table SMART
def insert_smart_data(smart_list):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        for data in smart_list:
            cursor.execute("""
            INSERT INTO smart_data (timestamp, disk_model, serial_number, temperature, power_on_hours, reallocated_sectors, read_errors, write_errors, disk_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data["timestamp"], data["disk_model"], data["serial_number"], data["temperature"],
                data["power_on_hours"], data["reallocated_sectors"], data["read_errors"],
                data["write_errors"], data["disk_status"]
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de l'insertion des données SMART : {e}")

# Insertion des logs dans la table logs
def insert_logs(logs):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        for log in logs:
            cursor.execute("""
            INSERT INTO event_logs (timestamp, log_type, event_id, source, level, message)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                log["timestamp"], log["log_type"], log["event_id"], log["source"], log["level"], log["message"]
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de l'insertion des logs : {e}")

# Exportation en CSV
def export_to_csv():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        for table in ["system_metrics", "smart_data", "event_logs"]:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
            df.to_csv(f"{table}.csv", index=False)
        conn.close()
    except Exception as e:
        logging.error(f"Erreur lors de l'exportation en CSV : {e}")

# Boucle principale de collecte
def monitor_system(interval=20):  # Par défaut, collecte toutes les 5 minutes
    setup_database()
    print("Monitoring en cours...")
    try:
        while True:
            metrics = get_system_metrics()
            if metrics:
                insert_metrics(metrics)

            smart_data = get_smart_data()
            if smart_data:
                insert_smart_data(smart_data)

            logs = get_windows_logs()
            if logs:
                insert_logs(logs)

            print(f"{metrics['timestamp']} - CPU: {metrics['cpu_usage']}%, RAM: {metrics['ram_usage']}%, Disque: {metrics['disk_usage']}%, Carte mère: {metrics['motherboard_temp']}°C")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Arrêt du monitoring.")
        #export_to_csv()
        from creation_dataset import create_dataset
        create_dataset()


if __name__ == "__main__":
    monitor_system()