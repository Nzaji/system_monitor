import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import requests
from datetime import datetime
import time
from threading import Thread

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    assets_folder="assets",

    suppress_callback_exceptions=True,
    meta_tags=[{
        'name':'viewport',
        'content':'width=device-width, initial-scale=1.0'
    }]
)

app.css.config.serve_locally=True
app.scripts.config.serve_locally=True
app.title = "Supervision des Pannes Informatiques"
server = app.server

# Configuration
COLOR_MAP = {
    'normal': '#2ecc71',
    'surcharge_cpu': '#e74c3c',
    'probleme_ram': '#e74c3c',
    'temperature_elevee': '#f39c12',
    'secteurs_defectueux': '#e74c3c',
    'erreurs_systeme': '#e74c3c',
    'avertissements_systeme': '#f39c12',
    'perte_paquets_reseau': '#e74c3c',
    'surchauffe_carte_mere': '#e74c3c',
    'surchauffe_gpu': '#e74c3c',
    'disque_fin_de_vie': '#f39c12',
    'batterie_faible': '#f39c12'
}

ICON_MAP = {
    'normal': 'fa-check-circle',
    'surcharge_cpu': 'fa-microchip',
    'probleme_ram': 'fa-memory',
    'temperature_elevee': 'fa-temperature-high',
    'secteurs_defectueux': 'fa-hdd',
    'erreurs_systeme': 'fa-bug',
    'avertissements_systeme': 'fa-exclamation-triangle',
    'perte_paquets_reseau': 'fa-network-wired',
    'surchauffe_carte_mere': 'fa-server',
    'surchauffe_gpu': 'fa-gamepad',
    'disque_fin_de_vie': 'fa-hard-drive',
    'batterie_faible': 'fa-battery-quarter'
}
LABEL_MAPPING = {
    0: 'normal',
    1: 'surcharge_cpu',
    2: 'probleme_ram',
    3: 'temperature_elevee',
    4: 'secteurs_defectueux',
    5: 'erreurs_systeme',
    6: 'avertissements_systeme',
    7: 'perte_paquets_reseau',
    8: 'surchauffe_carte_mere',
    9: 'surchauffe_gpu',
    10: 'disque_fin_de_vie',
    11: 'batterie_faible'
}

# Données initiales
current_data = {
    'prediction': 'normal',
    'confidence': 0,
    'timestamp': datetime.now().isoformat(),
    'features': [0]*9,
    'probabilities': {k: 0 for k in COLOR_MAP.keys()}
}

history_df = pd.DataFrame(columns=[
    'timestamp', 'prediction', 'confidence',
    'cpu_usage', 'ram_usage', 'disk_usage',
    'temperature', 'read_errors', 'write_errors',
    'reallocated_sectors'
])

# Layout
app.layout = dbc.Container(fluid=True, children=[
    dbc.Row(dbc.Col(html.H1("Tableau de Bord - Prédiction des Pannes", className="text-center my-4"))),
   
    dbc.Row([
        dbc.Col(width=8, children=[
            html.Div(id="main-alert", className="alert-main py-3")
        ]),
        dbc.Col(width=4, children=[
            dbc.Card([
                dbc.CardBody([
                    html.H4("Confiance", className="card-title"),
                    html.Div(id="confidence-kpi", className="display-4")
                ])
            ], color="secondary")
        ])
    ], className="mb-4"),
   
    dbc.Row([
        dbc.Col(md=4, children=[
            dbc.Card([
                dbc.CardHeader("Métriques Système"),
                dbc.CardBody([
                    html.Div(id="system-metrics", className="metrics-grid")
                ])
            ])
        ]),
        dbc.Col(md=8, children=[
            dbc.Card([
                dbc.CardHeader("Probabilités des Pannes"),
                dbc.CardBody([
                    dcc.Graph(id="probabilities-chart", config={'displayModeBar': False})
                ])
            ])
        ])
    ], className="mb-4"),
   
    dbc.Row([
        dbc.Col(md=6, children=[
            dbc.Card([
                dbc.CardHeader(
                    html.H4("Recommandations", className="mb-0"),
                    className="bg-primary text-white"
                ),
                dbc.CardBody([
                    html.Div(
                        id="recommendations-list",
                        style={'height': '300px'}
                    )
                ])
        ], style={'height': '100%'})
        ]),
        dbc.Col(md=6, children=[
            dbc.Card([
                dbc.CardHeader("Historique des Pannes"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='history-table',
                        columns=[
                            {'name': 'Heure', 'id': 'timestamp'},
                            {'name': 'Type', 'id': 'prediction'},
                            {'name': 'Confiance', 'id': 'confidence'},
                            {'name': 'CPU', 'id': 'cpu_usage'},
                            {'name': 'Temp', 'id': 'temperature'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'color': 'white',
                            'backgroundColor': '#222',
                            'border': '1px solid #444'
                        },
                        style_header={
                            'backgroundColor': '#375a7f',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#303030'
                            },
                            *[
                                {
                                    'if': {
                                        'filter_query': f'{{prediction}} = "{cls}"',
                                        'column_id': 'prediction'
                                    },
                                    'backgroundColor': COLOR_MAP[cls],
                                    'color': 'white'
                                } for cls in COLOR_MAP
                            ]
                        ],
                        page_size=8,
                        page_action='native'
                    )
                ])
            ])
        ])
    ]),
   
    dcc.Interval(id='update-interval', interval=10*1000, n_intervals=0),
    dcc.Store(id='data-store')
], style={'backgroundColor': '#222'})

def fetch_data():
    try:
        response = requests.get(
            'http://localhost:5000/api/status',
            timeout=5
        )
       
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                # Décodage de la prédiction si elle est numérique
                prediction = data['data'].get('prediction', 'normal')
                if isinstance(prediction, int):
                   prediction = LABEL_MAPPING.get(prediction, 'normal')
                
                # Mise à jour des données avec la prédiction décodée
                data['data']['prediction'] = prediction
                print('Données reçues avec succès')
                print(f"Réponse API brute: {response.text}")
                return data['data']
       
        print(f"Erreur: {response.status_code} - {response.text}")
        return None
       
    except Exception as e:
        print(f"Erreur de connexion: {e}")
        return None

def data_updater():
    global current_data, history_df
    
    # Table de correspondance ABSOLUE (à adapter selon vos classes réelles)
    LABEL_MAP = {
        0: 'normal',
        1: 'surcharge_cpu',
        2: 'probleme_ram',
        3: 'temperature_elevee',
        4: 'secteurs_defectueux',
        5: 'erreurs_systeme',
        6: 'avertissements_systeme',
        7: 'perte_paquets_reseau',
        8: 'surchauffe_carte_mere',
        9: 'surchauffe_gpu',
        10: 'disque_fin_de_vie',
        11: 'batterie_faible'
    }

    while True:
        try:
            # 1. Récupération des données
            new_data = fetch_data()
            
            if new_data:
                # 2. Debug: Afficher les données brutes reçues
                print("\n[DEBUG] Données brutes reçues:", new_data)
                
                # 3. Conversion IMPÉRATIVE de la prédiction
                prediction = new_data.get('prediction')
                
                # Cas 1: La prédiction est numérique (int)
                if isinstance(prediction, int):
                    new_data['prediction'] = LABEL_MAP.get(prediction, 'inconnu')
                
                # Cas 2: La prédiction est une chaîne numérique (ex: "2")
                elif isinstance(prediction, str) and prediction.isdigit():
                    new_data['prediction'] = LABEL_MAP.get(int(prediction), 'inconnu')
                
                # Cas 3: La prédiction est déjà en texte mais non reconnue
                elif isinstance(prediction, str) and prediction not in LABEL_MAP.values():
                    new_data['prediction'] = 'inconnu'
                
                # 4. Mise à jour des probabilités (si nécessaire)
                if 'probabilities' in new_data:
                    probs = new_data['probabilities']
                    # Convertir les clés numériques en texte
                    if any(isinstance(k, int) for k in probs.keys()):
                        new_probs = {
                            LABEL_MAP.get(int(k), f'inconnu_{k}'): float(v)
                            for k, v in probs.items()
                        }
                        new_data['probabilities'] = new_probs
                
                # 5. Debug: Afficher les données après conversion
                print("[DEBUG] Données après conversion:", new_data)
                
                # 6. Mise à jour des données globales
                current_data.update(new_data)
                
                # 7. Mise à jour de l'historique
                new_row = {
                    'timestamp': current_data.get('timestamp', datetime.now().isoformat()),
                    'prediction': current_data['prediction'],
                    'confidence': current_data.get('confidence', 0),
                    'cpu_usage': current_data.get('features', [0]*9)[0],
                    'ram_usage': current_data.get('features', [0]*9)[1],
                    'disk_usage': current_data.get('features', [0]*9)[2],
                    'temperature': current_data.get('features', [0]*9)[4],
                    'read_errors': current_data.get('features', [0]*9)[5],
                    'write_errors': current_data.get('features', [0]*9)[6],
                    'reallocated_sectors': current_data.get('features', [0]*9)[7]
                }
                
                global history_df
                history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
                
                # Garder seulement les 100 dernières entrées
                if len(history_df) > 100:
                    history_df = history_df.iloc[-100:]
            
            # Pause entre les mises à jour
            time.sleep(10)
            
        except Exception as e:
            print(f"[ERREUR] Dans data_updater: {str(e)}")
            time.sleep(10)  # Pause même en cas d'erreur

update_thread = Thread(target=data_updater, daemon=True)
update_thread.start()

# Callbacks
@app.callback(
    Output('main-alert', 'children'),
    Output('main-alert', 'style'),
    Input('update-interval', 'n_intervals')
)
def update_main_alert(n):
    pred = current_data['prediction']
    if isinstance(pred, int):
        
        LABEL_MAPPING = {
            0: 'normal',
            1: 'surcharge_cpu',
            2: 'probleme_ram',
            3: 'temperature_elevee',
            4: 'secteurs_defectueux',
            5: 'erreurs_systeme',
            6: 'avertissements_systeme',
            7: 'perte_paquets_reseau',
            8: 'surchauffe_carte_mere',
            9: 'surchauffe_gpu',
            10: 'disque_fin_de_vie',
            11: 'batterie_faible'
        }
        pred = LABEL_MAPPING.get(pred, 'inconnu')

    conf = current_data['confidence']
   
    alert_style = {
        'backgroundColor': COLOR_MAP.get(pred, '#7f8c8d'),
        'color': 'white',
        'border': 'none'
    }
   
    alert_content = [
        html.I(className=f"fas {ICON_MAP.get(pred, 'fa-question-circle')} me-2"),
        html.Span(f"{pred.upper()} - Confiance: {conf:.1f}%")
    ]
   
    return alert_content, alert_style

@app.callback(
    Output('confidence-kpi', 'children'),
    Input('update-interval', 'n_intervals')
)
def update_confidence_kpi(n):
    return f"{current_data['confidence']:.1f}%"



@app.callback(
    Output('system-metrics', 'children'),
    Input('update-interval', 'n_intervals')
)
def update_system_metrics(n):
    try:
        # =============================================
        # SECTION DEBUG - DONNÉES SIMULÉES (À ACTIVER/DÉSACTIVER)
        # =============================================
        debug_mode = True  # ← Mettre à False pour repasser en mode normal
        
        if debug_mode:
            from random import uniform, randint
            import time
            
            # Génère des données réalistes fluctuantes
            fake_data = [
                round(uniform(5, 95),1),          # CPU (%)
                round(uniform(30, 98),1),         # RAM (%)
                round(uniform(10, 90),1),         # Disk (%)
                randint(0, 2),                  # Niveau événement (0:Info, 1:Warning, 2:Error)
                round(uniform(30, 80)),         # Température (°C)
                randint(0, 15),                 # Read errors
                randint(0, 5),                  # Write errors
                randint(0, 30),                 # Bad sectors
                randint(1000, 5000)             # Event ID
            ]
            
            # Simule une légère variation à chaque update
            if hasattr(update_system_metrics, "last_fake_data"):
                for i in range(3):
                    fake_data[i] = round(fake_data[i] + uniform(-5, 5), 1)
            
            update_system_metrics.last_fake_data = fake_data
            
            features = fake_data
            print("=== MODE DEBUG ACTIF ===", features)  # Visible dans la console
        else:
            # Mode normal
            features = current_data.get('features', [0]*9)
            if len(features) < 9:
                features = [0]*9  # Sécurité
        # =============================================

        # Configuration des métriques (adaptez les seuils si besoin)
        METRICS = [
            {'name': 'CPU', 'value': features[0], 'unit': '%', 'icon': 'fa-microchip',
             'color': 'danger' if features[0] > 85 else 'warning' if features[0] > 70 else 'success'},
            
            {'name': 'RAM', 'value': features[1], 'unit': '%', 'icon': 'fa-memory',
             'color': 'danger' if features[1] > 90 else 'warning' if features[1] > 75 else 'success'},
            
            {'name': 'Disque', 'value': features[2], 'unit': '%', 'icon': 'fa-hdd',
             'color': 'danger' if features[2] > 85 else 'warning' if features[2] > 70 else 'success'},
            
            {'name': 'Température', 'value': features[4], 'unit': '°C', 'icon': 'fa-temperature-high',
             'color': 'danger' if features[4] > 70 else 'warning' if features[4] > 50 else 'success'},
            
            {'name': 'Erreurs Lecture', 'value': features[5], 'unit': '', 'icon': 'fa-exclamation-circle',
             'color': 'danger' if features[5] > 10 else 'warning' if features[5] > 5 else 'success'},
            
            {'name': 'Secteurs Défectueux', 'value': features[7], 'unit': '', 'icon': 'fa-exclamation-triangle',
             'color': 'danger' if features[7] > 20 else 'warning' if features[7] > 5 else 'success'}
        ]

        # Construction des cartes
        cards = []
        for metric in METRICS:
            cards.append(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className=f"fas {metric['icon']} me-2"),
                            metric['name']
                        ], className=f"bg-{metric['color']} text-white"),
                        dbc.CardBody([
                            html.H4(
                                f"{metric['value']}{metric['unit']}",
                                className="card-title text-center mb-0"
                            ),
                            html.Small(
                                'CRITIQUE' if metric['color'] == 'danger' else 
                                'ALERTE' if metric['color'] == 'warning' else 
                                'NORMAL',
                                className=f"text-{metric['color']} d-block text-center mt-1"
                            )
                        ], className="py-2")
                    ], className="h-100 shadow-sm"),
                    md=6, lg=4, className="mb-3"
                )
            )

        return dbc.Row(cards, className="g-3")

    except Exception as e:
        print(f"[ERREUR] update_system_metrics: {str(e)}")
        return dbc.Alert(
            [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Erreur d'affichage des métriques"
            ],
            color="danger"
        )

@app.callback(
    Output('probabilities-chart', 'figure'),
    Input('update-interval', 'n_intervals')
)

def update_probabilities_chart(n):
    try:
        # ========================
        # 1. CONFIGURATION GLOBALE
        # ========================
        
        # Table de correspondance complète (identique à celle de l'API)
        LABEL_MAPPING = {
            0: 'normal',
            1: 'surcharge_cpu',
            2: 'probleme_ram',
            3: 'temperature_elevee',
            4: 'secteurs_defectueux',
            5: 'erreurs_systeme',
            6: 'avertissements_systeme',
            7: 'perte_paquets_reseau',
            8: 'surchauffe_carte_mere',
            9: 'surchauffe_gpu',
            10: 'disque_fin_de_vie',
            11: 'batterie_faible'
        }

        # Palette de couleurs distinctes pour chaque classe
        COLOR_PALETTE = {
            'normal': '#2ecc71',          # Vert
            'surcharge_cpu': '#e74c3c',   # Rouge
            'probleme_ram': '#f39c12',    # Orange
            'temperature_elevee': '#d35400', # Orange foncé
            'secteurs_defectueux': '#c0392b', # Rouge foncé
            'erreurs_systeme': '#9b59b6',    # Violet
            'avertissements_systeme': '#f1c40f', # Jaune
            'perte_paquets_reseau': '#3498db',  # Bleu
            'surchauffe_carte_mere': '#e84393', # Rose
            'surchauffe_gpu': '#e17055',       # Saumon
            'disque_fin_de_vie': '#7f8c8d',    # Gris
            'batterie_faible': '#fdcb6e'       # Jaune clair
        }

        # ========================
        # 2. TRAITEMENT DES DONNÉES
        # ========================

        # Récupération des probabilités brutes
        raw_probs = current_data.get('probabilities', {})
        
        # Dictionnaire nettoyé
        clean_probs = {}

        # Conversion des clés et vérification
        for key, value in raw_probs.items():
            # Cas 1: Clé numérique (int)
            if isinstance(key, int):
                class_name = LABEL_MAPPING.get(key, f'inconnu_{key}')
                clean_probs[class_name] = float(value)
            
            # Cas 2: Clé string numérique ("2")
            elif isinstance(key, str) and key.isdigit():
                class_name = LABEL_MAPPING.get(int(key), f'inconnu_{key}')
                clean_probs[class_name] = float(value)
            
            # Cas 3: Clé déjà textuelle mais non reconnue
            elif key not in LABEL_MAPPING.values():
                clean_probs[f'erreur_{key}'] = float(value)
            
            # Cas 4: Clé textuelle valide
            else:
                clean_probs[key] = float(value)

        # Remplissage des classes manquantes
        for class_name in COLOR_PALETTE.keys():
            if class_name not in clean_probs:
                clean_probs[class_name] = 0.0

        # Debug critique
        print(f"[DEBUG] Probabilités finales : {clean_probs}")

        # ========================
        # 3. CRÉATION DU GRAPHIQUE
        # ========================

        # DataFrame avec ordre fixe
        df = pd.DataFrame({
            'Classe': list(COLOR_PALETTE.keys()),
            'Probabilité': [clean_probs[cls] for cls in COLOR_PALETTE.keys()],
            'Couleur': list(COLOR_PALETTE.values())
        })

        # Génération du graphique
        fig = px.bar(
            df,
            x='Classe',
            y='Probabilité',
            color='Classe',
            color_discrete_map=COLOR_PALETTE,
            text='Probabilité',
            category_orders={'Classe': list(COLOR_PALETTE.keys())}
        )

        # ========================
        # 4. PERSONNALISATION AVANCÉE
        # ========================

        # Style des barres
        fig.update_traces(
            marker_line_color='rgba(255,255,255,0.5)',
            marker_line_width=1.5,
            texttemplate='<b>%{y:.1f}%</b>',
            textposition='outside',
            textfont_size=14,
            opacity=0.9,
            hovertemplate='<b>%{x}</b><br>Probabilité: %{y:.2f}%<extra></extra>'
        )

        # Mise en page globale
        fig.update_layout(
            plot_bgcolor='#222',
            paper_bgcolor='#222',
            font={'family': 'Arial', 'color': 'white'},
            xaxis={
                'title': '',
                'tickangle': -45,
                'tickfont': {'size': 12},
                'type': 'category'  # Empêche l'ordre alphabétique
            },
            yaxis={
                'title': 'Probabilité (%)',
                'range': [0, max(clean_probs.values()) + 10 if clean_probs else 100],
                'gridcolor': 'rgba(255,255,255,0.1)'
            },
            showlegend=False,
            margin={'t': 40, 'b': 120, 'l': 60, 'r': 20},
            transition={'duration': 300}
        )

        return fig

    except Exception as e:
        print(f"[ERREUR CRITIQUE] {str(e)}")
        # Fallback visuel
        fig = px.bar()
        fig.update_layout(
            plot_bgcolor='#222',
            paper_bgcolor='#222',
            annotations=[{
                'text': 'Données temporairement indisponibles',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16, 'color': '#f39c12'}
            }]
        )
        return fig
    except Exception as e:
        print(f"[ERREUR] Graphique des probabilités: {str(e)}")
        return px.bar()  # Graphique vide si erreur

@app.callback(
    Output('recommendations-list', 'children'),
    Input('update-interval', 'n_intervals')
)
def update_recommendations(n):
    try:
        # 1. Récupération des données
        prediction = current_data.get('prediction', 'normal')
        features = current_data.get('features', [0]*9)
        
        # 2. Dictionnaire COMPLET des recommandations de base
        BASE_RECOMMENDATIONS = {
            'normal': [
                "✓ Système fonctionnant normalement",
                "Vérifier périodiquement les logs système"
            ],
            'surcharge_cpu': [
                "Arrêter les processus non essentiels",
                "Vérifier les tâches planifiées gourmandes en CPU",
                "Augmenter la ventilation du système",
                "Considérer une upgrade du processeur si fréquent"
            ],
            'probleme_ram': [
                "Fermer les applications inutilisées",
                "Vérifier les fuites mémoire avec un outil dédié",
                "Ajouter de la RAM si le problème persiste",
                "Optimiser les paramètres de mémoire virtuelle"
            ],
            'temperature_elevee': [
                "Nettoyer les ventilateurs et les aérations",
                "Vérifier le bon fonctionnement des ventilateurs",
                "Utiliser un support ventilé pour ordinateur portable",
                "Éviter les surfaces molles qui bloquent la ventilation"
            ],
            'secteurs_defectueux': [
                "Lancer une analyse complète du disque (chkdsk)",
                "Sauvegarder immédiatement les données critiques",
                "Remplacer le disque si >50 secteurs réalloués",
                "Éviter les arrêts brutaux qui endommagent le disque"
            ],
            'erreurs_systeme': [
                "Analyser les logs système (Event Viewer)",
                "Mettre à jour les pilotes et le système d'exploitation",
                "Exécuter un scan SFC (System File Checker)",
                "Considérer une restauration système si récurrent"
            ],
            'avertissements_systeme': [
                "Examiner les avertissements dans les logs",
                "Vérifier l'espace disque disponible",
                "Contrôler l'état des sauvegardes",
                "Mettre à jour les applications concernées"
            ],
            'perte_paquets_reseau': [
                "Redémarrer le routeur/modem",
                "Tester avec un câble Ethernet plutôt qu'en WiFi",
                "Vérifier les interférences réseau",
                "Mettre à jour les pilotes réseau"
            ],
            'surchauffe_carte_mere': [
                "Éteindre immédiatement le système si >85°C",
                "Vérifier le bon contact des dissipateurs thermiques",
                "Nettoyer les poussières dans le boîtier",
                "Consulter un technicien si le problème persiste"
            ],
            'surchauffe_gpu': [
                "Réduire la qualité graphique des applications",
                "Nettoyer les ventilateurs de la carte graphique",
                "Vérifier le bon fonctionnement du refroidissement",
                "Éviter les surclocks non stabilisés"
            ],
            'disque_fin_de_vie': [
                "Planifier immédiatement le remplacement du disque",
                "Migrer vers un SSD pour plus de fiabilité",
                "Vérifier l'état SMART régulièrement",
                "Ne pas stocker de données critiques dessus"
            ],
            'batterie_faible': [
                "Remplacer la batterie si capacité <60%",
                "Éviter les charges/décharges complètes",
                "Utiliser le mode économie d'énergie",
                "Conserver la batterie entre 20% et 80% pour prolonger sa durée"
            ],
            'inconnu': [
                "Diagnostic en cours...",
                "Vérifier les logs pour plus d'informations"
            ]
        }

        # 3. Récupération des recommandations de base
        recommendations = BASE_RECOMMENDATIONS.get(prediction, BASE_RECOMMENDATIONS['inconnu'])
        
        # 4. Ajout des recommandations contextuelles
        if len(features) >= 8:
            # Critères CPU
            cpu_usage = float(features[0])
            if cpu_usage > 90:
                recommendations.insert(0, "⚠️ CRITIQUE: CPU à {}% - Arrêt immédiat recommandé".format(cpu_usage))
            elif cpu_usage > 70:
                recommendations.insert(0, "⚠️ Attention: CPU à {}%".format(cpu_usage))
            
            # Critères température
            temp = float(features[4])
            if temp > 80:
                recommendations.insert(0, "🔥 CRITIQUE: Température à {}°C".format(temp))
            elif temp > 60:
                recommendations.insert(0, "🌡️ Attention: Température à {}°C".format(temp))
            
            # Critères disque
            sectors = float(features[7])
            if sectors > 50:
                recommendations.insert(0, "💾 URGENT: {} secteurs défectueux".format(sectors))
            elif sectors > 10:
                recommendations.insert(0, "💾 Avertissement: {} secteurs défectueux".format(sectors))

        # 5. Formatage HTML avec icônes et couleurs
        recommendation_items = []
        for rec in recommendations:
            # Détermination icône/couleur selon criticité
            if "CRITIQUE" in rec or "URGENT" in rec:
                icon = "fa-exclamation-circle"
                color = "text-danger"
            elif "Attention" in rec or "Avertissement" in rec:
                icon = "fa-exclamation-triangle"
                color = "text-warning"
            elif "✓" in rec:
                icon = "fa-check-circle"
                color = "text-success"
            else:
                icon = "fa-info-circle"
                color = "text-info"
            
            recommendation_items.append(
                html.Li(
                    [
                        html.I(className=f"fas {icon} me-2 {color}"),
                        html.Span(rec.replace("✓", "").strip())
                    ],
                    className="mb-2"
                )
            )

        return html.Ul(
            recommendation_items,
            className="list-unstyled mt-3",
            style={'fontSize': '1.1rem'}
        )

    except Exception as e:
        print(f"[ERREUR] update_recommendations: {str(e)}")
        return html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                "Système de recommandations temporairement indisponible"
            ],
            className="text-danger"
        )
@app.callback(
    Output('history-table', 'data'),
    Input('update-interval', 'n_intervals')
)
def update_history_table(n):
    if history_df.empty:
        return []
   
    df = history_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
    df['confidence'] = df['confidence'].apply(lambda x: f"{x:.1f}%")
    df['cpu_usage'] = df['cpu_usage'].apply(lambda x: f"{x:.1f}%")
    df['temperature'] = df['temperature'].apply(lambda x: f"{x:.1f}°C")
   
    return df.sort_values('timestamp', ascending=False).to_dict('records')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=True)
