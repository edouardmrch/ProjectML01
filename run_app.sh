#!/bin/bash

echo "Lancement de l'application de traduction de sous-titres..."

# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application Streamlit
streamlit run src/app.py 