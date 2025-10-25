import psutil
import time
import wmi
import win32evtlog
from datetime import datetime
import sys
import ctypes
import logging
import requests
import json
from strict_serializer import StrictEncoder
import pickle
import base64

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collector.log'),
        logging.StreamHandler()
    ]
)

# Configuration
API_URL = "http://localhost:5000/"
HEADERS = {'Content-Type': 'application/json'}
COLLECT_INTERVAL = 20
TIMEOUT = 15

# Mapping des niveaux d'événements
LEVEL_MAPPING = {
    'Information': 0,
    'Warning': 1,
    'Error': 2,
    'Audit Success': 0,
    'Audit Failure': 2
}

def get_system_metrics():
    try:
        metrics = {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'ram_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('C:').percent,
            'temperature': 0
        }

        try:
            w = wmi.WMI(namespace="root\\wmi")
            temp_info = w.MSAcpi_ThermalZoneTemperature()
            if temp_info:
                metrics['temperature'] = (temp_info[0].CurrentTemperature - 2732) / 10.0
        except Exception as e:
            logging.warning(f"Température non lue: {e}")

        return metrics
    except Exception as e:
        logging.error(f"Erreur métriques: {e}")
        return None

def get_disk_health():
    health = {
        'reallocated_sectors': 0,
        'read_errors': 0,
        'write_errors': 0
    }

    try:
        w = wmi.WMI(namespace="root\\wmi")
        disks = w.MSStorageDriver_FailurePredictStatus()
        if disks:
            smart_data = w.MSStorageDriver_ATAPISmartData()
            if smart_data:
                # Conversion IMMÉDIATE en int Python
                health.update({
                    'reallocated_sectors': int(int.from_bytes(smart_data[0].VendorSpecific[196:198], byteorder='little')),
                    'read_errors': int(int.from_bytes(smart_data[0].VendorSpecific[200:202], byteorder='little')),
                    'write_errors': int(int.from_bytes(smart_data[0].VendorSpecific[204:206], byteorder='little'))
                })
    except Exception as e:
        logging.warning(f"Erreur SMART: {e}")

    return health

def get_system_events():
    event = {'event_id': 0, 'level': 'Information'}

    try:
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0, 1)
      
        if events:
            event_type = events[0].EventType
            event['level'] = 'Error' if event_type == 1 else 'Warning' if event_type == 2 else 'Information'
            event['event_id'] = int(events[0].EventID)  # Conversion explicite
    except Exception as e:
        logging.warning(f"Erreur événements: {e}")

    return event


def prepare_payload():
    try:
        metrics = get_system_metrics()
        if not metrics:
            return None

        disk = get_disk_health()
        event = get_system_events()

        # Conversion en types natifs
        payload = {
            'features': [
                float(str(metrics['cpu_usage'])),   # Conversion en 3 étapes
                float(str(metrics['ram_usage'])),
                float(str(metrics['disk_usage'])),
                int(float(str(LEVEL_MAPPING.get(event['level'], 0)))),
                float(str(metrics['temperature'])),
                int(float(str(disk['read_errors']))),
                int(float(str(disk['write_errors']))),
                int(float(str(disk['reallocated_sectors']))),
                int(float(str(event['event_id'])))
            ],
            'timestamp': datetime.now().isoformat()
        }

        # Vérification paranoïaque
        for val in payload['features']:
            if not isinstance(val, (int, float)):
                raise TypeError(f"Type non natif détecté: {type(val)}")

        return payload
    except Exception as e:
        logging.error(f"ERREUR FATALE préparation: {str(e)}")
        return None


def send_to_api(payload):
    try:
        # Structure finale garantie
        api_payload = {
            "features": [float(x) for x in payload['features']],  # Conversion absolue en float
            "timestamp": payload.get('timestamp', datetime.now().isoformat())
        }
        # Debug: vérification des types
        types_check = [type(x) for x in api_payload['features']]
        if any(t not in (int, float) for t in types_check):
            logging.warning(f"Types non natifs détectés: {types_check}")
            api_payload['features'] = [float(x) for x in api_payload['features']]

        # Vérification de sécurité
        if len(api_payload['features']) != 9:
            raise ValueError("Nombre incorrect de features")

        response = requests.post(
            API_URL + "/predict",
            json=api_payload,  # Utilisez 'json=' au lieu de 'data='
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            print('donnée bien envoyée au serveur')
            return True
        logging.error(f"Erreur API ({response.status_code}): {response.text}")
    except Exception as e:
        logging.error(f"ERREUR: {str(e)}")
    return False


def main():
    logging.info("Démarrage du collector...")
   
    try:
        while True:
            start_time = time.time()
            payload = prepare_payload()
           
            if payload:
                
                send_to_api(payload)
           
            elapsed = time.time() - start_time
            sleep_time = max(0, COLLECT_INTERVAL - elapsed)
            time.sleep(sleep_time)
           
    except KeyboardInterrupt:
        logging.info("Arrêt manuel")
    except Exception as e:
        logging.error(f"Erreur inattendue: {e}")
    finally:
        logging.info("Collector arrêté")

if __name__ == '__main__':
    main()
