@echo off
echo Installation des dependances avec options speciales pour resoudre les problemes...

REM Activer l'environnement virtuel si present
if exist venv\ (
    call venv\Scripts\activate.bat
)

REM Installer les dependances de base
pip install pysrt==1.1.2 tqdm==4.66.2 requests==2.31.0

REM Installer pyarrow avec option speciale
echo Installation de pyarrow...
pip install --no-binary :all: pyarrow==11.0.0

REM Installer streamlit
echo Installation de streamlit...
pip install streamlit==1.33.0

echo.
echo Installation terminee.
echo Vous pouvez maintenant lancer l'application avec run_app.bat

pause 