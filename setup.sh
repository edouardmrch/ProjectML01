#!/bin/bash

# Détection de Python 3
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    # Vérifier la version
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f1)
    if [ "$PYTHON_VERSION" -eq 3 ]; then
        PYTHON=python
    else
        echo "Python 3 est requis mais n'a pas été trouvé."
        echo "Veuillez installer Python 3 et réessayer."
        exit 1
    fi
else
    echo "Python 3 est requis mais n'a pas été trouvé."
    echo "Veuillez installer Python 3 et réessayer."
    exit 1
fi

echo "Utilisation de $PYTHON"

# Créer un environnement virtuel
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    $PYTHON -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Créer le dossier pour les traductions
mkdir -p srt-files-traduits

echo ""
echo "L'environnement est prêt !"
echo "Pour commencer, placez vos fichiers SRT dans le dossier 'srt-files',"
echo "puis exécutez: python src/main.py"
echo ""
echo "Pour activer l'environnement, exécutez: source venv/bin/activate" 