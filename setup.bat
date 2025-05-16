@echo off
echo Configuration de l'environnement pour le traducteur de sous-titres SRT...

REM Vérifier la version de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python 3 et réessayer.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info.major == 3 else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3 est requis mais une autre version a été trouvée.
    echo Veuillez installer Python 3 et réessayer.
    pause
    exit /b 1
)

REM Créer l'environnement virtuel s'il n'existe pas
if not exist venv\ (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Installer les dépendances
echo Installation des dépendances...
pip install -r requirements.txt

REM Créer le dossier pour les traductions
if not exist srt-files-traduits mkdir srt-files-traduits

echo.
echo L'environnement est prêt !
echo Pour commencer, placez vos fichiers SRT dans le dossier 'srt-files',
echo puis exécutez: python src/main.py
echo.
echo Pour activer l'environnement, exécutez: venv\Scripts\activate.bat
pause 