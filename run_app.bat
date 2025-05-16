@echo off
echo Lancement de l'application de traduction de sous-titres...

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Lancer l'application Streamlit
streamlit run src/app_srt_translator.py

pause 