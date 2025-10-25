import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import numpy as np
import joblib

# Charger le modèle et l'encodeur
model = joblib.load('ml_randomforest.pkl')
label_encoder = joblib.load('label_encoder.pkl')  # Pour la target (11 classes)
level_encoder = joblib.load('level_encoder.pkl')  # Pour la feature 'level' (3 classes)


val1=22
val2="firmin"
# Créer l'application Dash
app = dash.Dash(__name__)

# Layout de l'application
app.layout = html.Div([
    html.H1("Tableau de bord de prédiction", className="title1"),

    # Formulaire pour saisir les données
    html.Div([
        html.Label("cpu usage (Numérique)"),
        dcc.Input(id='cpu_usage', type='number', value=val1),
        html.Br(),

        html.Label("ram usage (Numérique)"),
        dcc.Input(id='ram_usage', type='number', value=val1),
        html.Br(),

        html.Label("disk usage (Numérique)"),
        dcc.Input(id='disk_usage', type='number', value=val1),
        html.Br(),

        html.Label("temperature (Numérique)"),
        dcc.Input(id='temperature', type='number', value=val1),
        html.Br(),

        html.Label("reallocated sectors (Numérique)"),
        dcc.Input(id='reallocated_sectors', type='number', value=val1),
        html.Br(),

        html.Label("read_errors (Numérique)"),
        dcc.Input(id='read_errors', type='number', value=val1),
        html.Br(),

        html.Label("write_errors (Numérique)"),
        dcc.Input(id='write_errors', type='number', value=val1),
        html.Br(),

        html.Label("event_id (Numérique)"),
        dcc.Input(id='event_id', type='number', value=val1),
        html.Br(),
        html.Label("level (Catégoriel)"),
        dcc.Input(id='level', type='text', value=val2),
        html.Br(),

        html.Button('Prédire', id='predict-button', n_clicks=0),
    ]),

    # Affichage des résultats
    html.Div(id='prediction-output')
])

# Callback pour faire la prédiction et afficher les résultats
@app.callback(
    Output('prediction-output', 'children'),
    [Input('predict-button', 'n_clicks')],
    [State('cpu_usage', 'value'),
     State('ram_usage', 'value'),
     State('disk_usage', 'value'),
     State('level', 'value'),
     State('temperature', 'value'),
     State('read_errors', 'value'),
     State('write_errors', 'value'),
     State('reallocated_sectors', 'value'),
     State('event_id', 'value')]
)
def update_output(n_clicks, cpu_usage, ram_usage, disk_usage, level, temperature, read_errors, write_errors, reallocated_sectors, event_id):
    if n_clicks > 0:
         # Encodage de 'level' avec le bon encodeur
        level_encoded = level_encoder.transform([level])[0]  # [!] Peut lever une erreur si valeur inconnue
        # Créer une ligne de données à partir des inputs
        new_data = pd.DataFrame({
            'cpu_usage': [cpu_usage],
            'ram_usage': [ram_usage],
            'disk_usage': [disk_usage],
            'level': [level],
            'temperature': [temperature],
            'read_errors': [read_errors],
            'write_errors': [write_errors],
            'reallocated_sectors': [reallocated_sectors],
            'event_id': [event_id],
            
        })

        # Faire la prédiction
         # Prédiction et décodage avec label_encoder
        y_pred_encoded = model.predict(new_data)
        y_pred_text = label_encoder.inverse_transform(y_pred_encoded)  # Décodage de la target
        y_pred_proba = model.predict_proba(new_data)


        # Convertir les probabilités en pourcentages
        y_pred_proba_percent = y_pred_proba * 100

        # Afficher les résultats
        results = html.Div([
            html.H3("Résultats de la prédiction :"),
            html.P(f"Prédiction : {y_pred_text[0]}"),
            html.H4("Probabilités :"),
           *[html.P(f"Probabilité de {label_encoder.classes_[i]} : {y_pred_proba_percent[0][i]:.2f}%")
           for i in range(len(label_encoder.classes_))]
        ])

        return results

# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True)
