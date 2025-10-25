import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Nombre d'exemples par classe
n_examples_per_class = 2500

# Liste des classes
classes = [
    "normal", "surcharge_cpu", "probleme_ram", "temperature_elevee",
    "secteurs_defectueux", "erreurs_systeme", "avertissements_systeme",
    "perte_paquets_reseau", "surchauffe_carte_mere", "surchauffe_gpu",
    "disque_fin_de_vie", "batterie_faible"
]

# Fonction pour générer des données pour une classe donnée
def generate_data_for_class(class_name, n_examples):
    data = []
    for _ in range(n_examples):
        if class_name == "normal":
            # Données normales
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 50),
                "ram_usage": np.random.uniform(0, 70),
                "disk_usage": np.random.uniform(0, 70),
                "temperature": np.random.uniform(20, 50),
                "reallocated_sectors": 0,
                "read_errors": 0,
                "write_errors": 0,
                "event_id": 0,
                "message": "Aucune erreur détectée.",
                "level": "Information",
                "label": "normal",
                "description": "Tout va bien.",
                "recommendation": "Aucune action requise."
            }
        elif class_name == "surcharge_cpu":
            # Données pour surcharge CPU
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(85, 100),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(50, 70),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 2),
                "write_errors": np.random.randint(0, 2),
                "event_id": 1001,
                "message": "Surcharge CPU détectée.",
                "level": "Error",
                "label": "surcharge_cpu",
                "description": "Surcharge CPU détectée (>85%).",
                "recommendation": "Vérifier les processus consommateurs de CPU."
            }
        elif class_name == "probleme_ram":
            # Données pour problème de RAM
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(90, 100),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(50, 70),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 2),
                "write_errors": np.random.randint(0, 2),
                "event_id": 1002,
                "message": "Pagefile utilisation excessive.",
                "level": "Error",
                "label": "probleme_ram",
                "description": "Utilisation excessive de la RAM (>90%).",
                "recommendation": "Fermer les applications inutiles ou augmenter la RAM."
            }
        elif class_name == "temperature_elevee":
            # Données pour température élevée
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(60, 100),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 2),
                "write_errors": np.random.randint(0, 2),
                "event_id": 1003,
                "message": "Température anormale du système.",
                "level": "Warning",
                "label": "temperature_elevee",
                "description": "Température anormale du système (>60°C).",
                "recommendation": "Vérifier le refroidissement et nettoyer les ventilateurs."
            }
        elif class_name == "secteurs_defectueux":
            # Données pour secteurs défectueux
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(6, 100),
                "read_errors": np.random.randint(0, 10),
                "write_errors": np.random.randint(0, 10),
                "event_id": 1004,
                "message": "Secteurs réalloués détectés.",
                "level": "Error",
                "label": "secteurs_defectueux",
                "description": "Secteurs réalloués détectés (>5).",
                "recommendation": "Surveiller l’état du disque dur et prévoir un remplacement."
            }
        elif class_name == "erreurs_systeme":
            # Données pour erreurs système
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(5, 20),
                "write_errors": np.random.randint(5, 20),
                "event_id": 1005,
                "message": "Nombre d'erreurs système critique.",
                "level": "Error",
                "label": "erreurs_systeme",
                "description": "Nombre d'erreurs système critique (>5).",
                "recommendation": "Vérifier les journaux d’événements Windows pour identifier les erreurs."
            }
        elif class_name == "avertissements_systeme":
            # Données pour avertissements système
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1006,
                "message": "Nombre élevé d'avertissements système.",
                "level": "Warning",
                "label": "avertissements_systeme",
                "description": "Nombre élevé d'avertissements système (>10).",
                "recommendation": "Analyser les avertissements pour prévenir d’éventuelles pannes."
            }
        elif class_name == "perte_paquets_reseau":
            # Données pour perte de paquets réseau
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1007,
                "message": "Perte de paquets réseau détectée.",
                "level": "Error",
                "label": "perte_paquets_reseau",
                "description": "Perte de paquets réseau (>5%).",
                "recommendation": "Vérifier la connexion réseau et le matériel réseau."
            }
        elif class_name == "surchauffe_carte_mere":
            # Données pour surchauffe carte mère
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(70, 100),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1008,
                "message": "Température anormale de la carte mère.",
                "level": "Error",
                "label": "surchauffe_carte_mere",
                "description": "Température anormale de la carte mère (>70°C).",
                "recommendation": "Vérifier le refroidissement de la carte mère."
            }
        elif class_name == "surchauffe_gpu":
            # Données pour surchauffe GPU
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(85, 100),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1009,
                "message": "Température anormale du GPU.",
                "level": "Error",
                "label": "surchauffe_gpu",
                "description": "Température anormale du GPU (>85°C).",
                "recommendation": "Vérifier le refroidissement du GPU."
            }
        elif class_name == "disque_fin_de_vie":
            # Données pour disque en fin de vie
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1010,
                "message": "Disque dur en fin de vie.",
                "level": "Warning",
                "label": "disque_fin_de_vie",
                "description": "Disque dur en fin de vie (>50000 heures).",
                "recommendation": "Prévoir le remplacement du disque dur."
            }
        elif class_name == "batterie_faible":
            # Données pour batterie faible
            row = {
                "timestamp": datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                "cpu_usage": np.random.uniform(0, 85),
                "ram_usage": np.random.uniform(0, 90),
                "disk_usage": np.random.uniform(0, 90),
                "temperature": np.random.uniform(20, 60),
                "reallocated_sectors": np.random.randint(0, 5),
                "read_errors": np.random.randint(0, 5),
                "write_errors": np.random.randint(0, 5),
                "event_id": 1011,
                "message": "Batterie faible détectée.",
                "level": "Warning",
                "label": "batterie_faible",
                "description": "Batterie faible (<80% de santé).",
                "recommendation": "Remplacer la batterie si nécessaire."
            }
        data.append(row)
    return pd.DataFrame(data)

# Génération des données pour toutes les classes
df_list = []
for class_name in classes:
    df_list.append(generate_data_for_class(class_name, n_examples_per_class))

# Concaténation des données
df = pd.concat(df_list, ignore_index=True)

# Sauvegarde en Excel
df.to_excel("good_dataset.xlsx", index=False)

print("Dataset généré avec succès et sauvegardé sous 'augmented_dataset.xlsx'.")