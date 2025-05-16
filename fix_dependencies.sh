#!/bin/bash

echo "Installation des dépendances avec options spéciales pour résoudre les problèmes..."

# Activer l'environnement virtuel si présent
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Installer les dépendances de base
pip install pysrt==1.1.2 tqdm==4.66.2 requests==2.31.0

# Installer pyarrow avec option spéciale
echo "Installation de pyarrow..."
pip install --no-binary :all: pyarrow==11.0.0

# Installer streamlit
echo "Installation de streamlit..."
pip install streamlit==1.33.0

echo ""
echo "Installation terminée."
echo "Vous pouvez maintenant lancer l'application avec ./run_app.sh" 