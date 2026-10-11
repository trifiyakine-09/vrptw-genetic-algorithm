@echo off
rem Se placer a la racine du projet, quel que soit le dossier de lancement
cd /d "%~dp0"

echo ==============================
echo   VRPTW Genetic Algorithm
echo ==============================

IF NOT EXIST venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating environment...
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt

echo Launching app...
python -m streamlit run src\interface.py

pause
