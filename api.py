from flask import Flask, request, jsonify
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from flask_cors import CORS
import joblib
from sklearn.preprocessing import LabelEncoder
import os

# Configuration de l'application
app = Flask(__name__)
CORS(app)  # Activation CORS pour le dashboard


# Configuration du logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

# Chargement des artefacts ML
try:
    # Essai avec les extensions .joblib d'abord
    try:
        label_encoder = joblib.load('label_encoder.joblib')
        model = joblib.load('ml_randomforest.joblib')
        print("Chargement réussi depuis .joblib!")
    except:
        # Fallback pour les extensions .pkl
        label_encoder = joblib.load('label_encoder.pkl')
        model = joblib.load('ml_randomforest.joblib')
        print("Chargement réussi depuis .pkl!")
   
    print("Classes disponibles:", list(label_encoder.classes_))
   
except Exception as e:
    print("ÉCHEC du chargement avec joblib:", str(e))
   
    # Solution de secours
    if 'label_encoder' not in locals():
        label_encoder = LabelEncoder()
        label_encoder.classes_ = np.array(['normal', 'surcharge_cpu', 'probleme_ram',
                                         'temperature_elevee', 'secteurs_defectueux',
                                         'erreurs_systeme', 'avertissements_systeme',
                                         'perte_paquets_reseau', 'surchauffe_carte_mere',
                                         'surchauffe_gpu', 'disque_fin_de_vie',
                                         'batterie_faible'])
       
        # Créer un modèle minimal si nécessaire
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier()
        print("Utilisation d'un modèle par défaut!")

# Configuration des classes
CLASS_CONFIG = {
    "normal": {"color": "success", "icon": "fa-check-circle"},
    "surcharge_cpu": {"color": "danger", "icon": "fa-microchip"},
    "probleme_ram": {"color": "danger", "icon": "fa-memory"},
    "temperature_elevee": {"color": "warning", "icon": "fa-temperature-high"},
    "secteurs_defectueux": {"color": "danger", "icon": "fa-hdd"},
    "erreurs_systeme": {"color": "danger", "icon": "fa-bug"},
    "avertissements_systeme": {"color": "warning", "icon": "fa-exclamation-triangle"},
    "perte_paquets_reseau": {"color": "danger", "icon": "fa-network-wired"},
    "surchauffe_carte_mere": {"color": "danger", "icon": "fa-server"},
    "surchauffe_gpu": {"color": "danger", "icon": "fa-gamepad"},
    "disque_fin_de_vie": {"color": "warning", "icon": "fa-hard-drive"},
    "batterie_faible": {"color": "warning", "icon": "fa-battery-quarter"}
}

@app.route('/')
def home():
    """Page d'accueil de l'API"""
    return """
    <h1>API de Prédiction des Pannes</h1>
    <p>Endpoints disponibles:</p>
    <ul>
        <li><b>POST /predict</b> - Recevoir les prédictions</li>
        <li><b>GET /health</b> - Vérifier l'état du service</li>
        <li><b>GET /classes</b> - Liste des classes supportées</li>
    </ul>
    """

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint principal pour les prédictions"""
    global last_prediction
    try:
        # Debug: Affiche les données reçues
        logging.info(f"Données reçues: {request.data}")
       
        data = request.get_json()
        if not data or 'features' not in data:
            logging.error(f"Format invalide. Données reçues: {data}")
            return jsonify({'error': 'Données manquantes ou format invalide'}), 400
        if data:
            print('données bien reçcu')
        # Vérification des features
        features = data['features']
        if len(features) != 9:
            logging.warning(f"Nombre incorrect de features: {len(features)}")
            return jsonify({'error': '9 features attendues'}), 400
       
        # Création du DataFrame
        X = pd.DataFrame([features], columns=[
            'cpu_usage', 'ram_usage', 'disk_usage', 'level',
            'temperature', 'read_errors', 'write_errors',
            'reallocated_sectors', 'event_id'
        ])
       
        # Conversion des types
        try:
            X = X.astype({
                'cpu_usage': 'float64',
                'ram_usage': 'float64',
                'disk_usage': 'float64',
                'level': 'int64',
                'temperature': 'float64',
                'read_errors': 'int64',
                'write_errors': 'int64',
                'reallocated_sectors': 'int64',
                'event_id': 'int64'
            })
        except Exception as e:
            logging.error(f"Erreur de conversion: {str(e)}")
            return jsonify({'error': 'Types de données invalides'}), 400
       
        # Prédiction
        prediction = model.predict(X)[0]
        prediction_label = label_encoder.inverse_transform([prediction])[0]
        probabilities = model.predict_proba(X)[0]
       
        def convert_numpy_types(obj):
            """Convertit récursivement les types NumPy en types natifs Python"""
            if isinstance(obj, (np.integer)):
                return int(obj)
            elif isinstance(obj, (np.floating)):
                return float(obj)
            elif isinstance(obj, (np.ndarray, np.generic)):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_numpy_types(v) for v in obj]
            return obj

        # Formatage de la réponse
        response = {
            'status': 'success',
            'prediction': str(prediction_label),  # Conversion explicite
            'confidence': float(round(np.max(probabilities) * 100, 2)),
            'probabilities': {
                str(cls): float(round(prob * 100, 2))  # Conversion explicite
                for cls, prob in zip(label_encoder.classes_, probabilities)
            },
            'recommendations': generate_recommendations(prediction_label, X.iloc[0].to_dict()),
            'icon': CLASS_CONFIG.get(prediction_label, {}).get('icon', 'fa-question-circle'),
            'color': CLASS_CONFIG.get(prediction_label, {}).get('color', 'secondary'),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
       
        response_converted=convert_numpy_types(response)
        last_prediction = response_converted  # Stocke la dernière prédiction
        logging.info(f"Prédiction réussie: {prediction_label}")
        if last_prediction:
            print('la prediction a reussi')
        return jsonify(response_converted)
       
    except Exception as e:
        logging.error(f"Erreur lors de la prédiction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Erreur interne du serveur',
            'details': str(e)
        }), 500

def generate_recommendations(prediction_label, features):
    """Génère des recommandations personnalisées"""
    recommendations = []
    thresholds = {
        'cpu': {'warning': 85, 'critical': 95},
        'ram': {'warning': 90, 'critical': 95},
        'temp': {'warning': 60, 'critical': 80},
        'sectors': {'warning': 10, 'critical': 50},
        'errors': {'warning': 5, 'critical': 20}
    }
   
    # Recommandations spécifiques
    if prediction_label == "surcharge_cpu":
        recommendations.append("Vérifier les processus CPU")
        if features['cpu_usage'] > thresholds['cpu']['critical']:
            recommendations.append("➜ Arrêt immédiat des processus non essentiels!")
   
    elif prediction_label == "probleme_ram":
        recommendations.append("Fermer les applications inutiles")
        if features['ram_usage'] > thresholds['ram']['critical']:
            recommendations.append("➜ Upgrade de RAM urgent requis!")
   
    elif prediction_label == "temperature_elevee":
        recommendations.append("Nettoyer les ventilateurs")
        if features['temperature'] > thresholds['temp']['critical']:
            recommendations.append("➜ Arrêt immédiat pour éviter les dommages!")
   
    elif prediction_label == "secteurs_defectueux":
        recommendations.append("Surveiller l'état du disque")
        if features['reallocated_sectors'] > thresholds['sectors']['critical']:
            recommendations.append("➜ Remplacer le disque immédiatement!")
   
    elif prediction_label == "erreurs_systeme":
        recommendations.append("Analyser les logs système")
        if features['read_errors'] > thresholds['errors']['critical']:
            recommendations.append("➜ Intervention technique nécessaire!")
   
    elif prediction_label == "avertissements_systeme":
        recommendations.append("Examiner les avertissements")
   
    elif prediction_label == "perte_paquets_reseau":
        recommendations.append("Vérifier le réseau")
   
    elif prediction_label == "surchauffe_carte_mere":
        recommendations.append("Vérifier le refroidissement")
        if features['temperature'] > 85:
            recommendations.append("➜ Arrêt immédiat requis!")
   
    elif prediction_label == "surchauffe_gpu":
        recommendations.append("Réduire la charge GPU")
        if features['temperature'] > 90:
            recommendations.append("➜ Arrêt des applications graphiques!")
   
    elif prediction_label == "disque_fin_de_vie":
        recommendations.append("Planifier le remplacement")
   
    elif prediction_label == "batterie_faible":
        recommendations.append("Remplacer la batterie")
   
    elif prediction_label == "normal":
        recommendations.append("Aucune action requise")
   
    # Recommandations supplémentaires
    if features['cpu_usage'] > thresholds['cpu']['warning'] and prediction_label != "surcharge_cpu":
        recommendations.append(f"CPU élevé ({features['cpu_usage']}%) - surveiller")
   
    if features['temperature'] > thresholds['temp']['warning'] and "temperature" not in prediction_label:
        recommendations.append(f"Température élevée ({features['temperature']}°C)")
   
    return recommendations
# Stockage des dernières données
last_prediction = None

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Endpoint pour le dashboard - Renvoie les dernières données"""
    if last_prediction is None:
        return jsonify({'error': 'Aucune donnée disponible'}), 404
   
    return jsonify({
        'status': 'success',
        'data': last_prediction,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de vérification de santé"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None,
        'api_version': '1.0.0'
    })

@app.route('/classes', methods=['GET'])
def list_classes():
    """Liste des classes supportées"""
    return jsonify({
        'classes': list(label_encoder.classes_),
        'count': len(label_encoder.classes_)
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)