import mysql.connector
import pandas as pd
import numpy as np
from datetime import timedelta

# Configuration MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "system_prediction"
}

# Création de dataset structuré
def create_dataset():
    conn = mysql.connector.connect(**DB_CONFIG)

    # Récupération des données des trois tables
    metrics = pd.read_sql("SELECT * FROM system_metrics", conn)
    smart = pd.read_sql("SELECT * FROM smart_data", conn)
    logs = pd.read_sql("SELECT * FROM event_logs", conn)

    conn.close()

    # Conversion des timestamps en datetime
    metrics['timestamp'] = pd.to_datetime(metrics['timestamp'])
    smart['timestamp'] = pd.to_datetime(smart['timestamp'])
    logs['timestamp'] = pd.to_datetime(logs['timestamp'])

    # Agrégation par minute sur les colonnes numériques uniquement avec index sur timestamp
    metrics_grouped = metrics.set_index('timestamp').select_dtypes(include='number').resample('1min').mean().reset_index()
    smart_grouped = smart.set_index('timestamp').select_dtypes(include='number').resample('1min').mean().reset_index()

    # Agrégation des logs (compter les erreurs et warnings)
    logs_grouped = logs.resample('1min', on='timestamp').agg({
        'event_id': 'count',
        'message': lambda x: ' | '.join(set(x.dropna())),
        'level': lambda x: ', '.join(set(x.dropna()))
    }).reset_index()

    # Fusion des données agrégées avec des suffixes pour éviter les conflits
    dataset = pd.merge(metrics_grouped, smart_grouped, on='timestamp', how='outer', suffixes=('_metrics', '_smart'))
    dataset = pd.merge(dataset, logs_grouped, on='timestamp', how='outer', suffixes=('', '_logs'))

    # Remplacement des NaN par 0 (en cas d'absence de logs associés)
    dataset.fillna(0, inplace=True)

    # Création de la colonne label avec des classes multiples
    dataset['label'] = 'normal'  # Par défaut, tout est normal

    # Définition des classes de pannes
    if 'cpu_usage' in dataset.columns:
        dataset.loc[(dataset['cpu_usage'] > 85) & (dataset['cpu_usage'].rolling(window=5).mean() > 85), 'label'] = 'surcharge_cpu'
    if 'ram_usage' in dataset.columns and 'message' in dataset.columns:
        dataset.loc[(dataset['ram_usage'] > 90) & dataset['message'].str.contains('Pagefile', case=False, na=False), 'label'] = 'probleme_ram'
    if 'temperature' in dataset.columns:
        dataset.loc[dataset['temperature'] > 60, 'label'] = 'temperature_elevee'
    if 'reallocated_sectors' in dataset.columns:
        dataset.loc[dataset['reallocated_sectors'] > 5, 'label'] = 'secteurs_defectueux'
    if 'error_count' in dataset.columns:
        dataset.loc[dataset['error_count'] >= 5, 'label'] = 'erreurs_systeme'
    if 'warning_count' in dataset.columns:
        dataset.loc[dataset['warning_count'] >= 10, 'label'] = 'avertissements_systeme'
    if 'network_packets_lost' in dataset.columns:
        dataset.loc[dataset['network_packets_lost'] > 5, 'label'] = 'perte_paquets_reseau'
    if 'motherboard_temp' in dataset.columns:
        dataset.loc[dataset['motherboard_temp'] > 70, 'label'] = 'surchauffe_carte_mere'
    if 'gpu_temp' in dataset.columns:
        dataset.loc[dataset['gpu_temp'] > 85, 'label'] = 'surchauffe_gpu'
    if 'power_on_hours' in dataset.columns:
        dataset.loc[dataset['power_on_hours'] > 50000, 'label'] = 'disque_fin_de_vie'
    if 'battery_health' in dataset.columns:
        dataset.loc[dataset['battery_health'] < 80, 'label'] = 'batterie_faible'

    # Ajout d'une colonne description et recommandation
    def generate_description(row):
        if row['label'] == 'normal':
            return "Tout va bien", "Aucune action requise."
      
        reasons = []
        recommendations = []

        if row['label'] == 'surcharge_cpu':
            reasons.append("Surcharge CPU détectée (>85%)")
            recommendations.append("Vérifier les processus consommateurs de CPU et optimiser les tâches.")
        if row['label'] == 'probleme_ram':
            reasons.append("Utilisation excessive de la RAM (>90%)")
            recommendations.append("Fermer les applications inutiles ou augmenter la RAM.")
        if row['label'] == 'temperature_elevee':
            reasons.append("Température anormale du système (>60°C)")
            recommendations.append("Vérifier le refroidissement et nettoyer les ventilateurs.")
        if row['label'] == 'secteurs_defectueux':
            reasons.append("Secteurs réalloués détectés (>5)")
            recommendations.append("Surveiller l’état du disque dur et prévoir un remplacement.")
        if row['label'] == 'erreurs_systeme':
            reasons.append("Nombre d'erreurs système critique (>5)")
            recommendations.append("Vérifier les journaux d’événements Windows pour identifier les erreurs.")
        if row['label'] == 'avertissements_systeme':
            reasons.append("Nombre élevé d'avertissements système (>10)")
            recommendations.append("Analyser les avertissements pour prévenir d’éventuelles pannes.")
        if row['label'] == 'perte_paquets_reseau':
            reasons.append("Perte de paquets réseau (>5%)")
            recommendations.append("Vérifier la connexion réseau et le matériel réseau.")
        if row['label'] == 'surchauffe_carte_mere':
            reasons.append("Température anormale de la carte mère (>70°C)")
            recommendations.append("Vérifier le refroidissement de la carte mère.")
        if row['label'] == 'surchauffe_gpu':
            reasons.append("Température anormale du GPU (>85°C)")
            recommendations.append("Vérifier le refroidissement du GPU.")
        if row['label'] == 'disque_fin_de_vie':
            reasons.append("Disque dur en fin de vie (>50000 heures)")
            recommendations.append("Prévoir le remplacement du disque dur.")
        if row['label'] == 'batterie_faible':
            reasons.append("Batterie faible (<80% de santé)")
            recommendations.append("Remplacer la batterie si nécessaire.")
      
        return " | ".join(reasons), " | ".join(recommendations)
  
    dataset[['description', 'recommendation']] = dataset.apply(generate_description, axis=1, result_type="expand")

    # Export en CSV et Excel
    dataset.to_csv('data.csv', index=False)
    dataset.to_excel('data.xlsx', index=False)

    print("Dataset avancé prêt et exporté avec classification multiple sous 'final_dataset_multiclass.xlsx'")

if __name__ == "__main__":
    create_dataset()