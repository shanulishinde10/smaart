@echo off
cd /d "%~dp0backend"
echo Installing dependencies (alternative - using deepface)...
pip install -r requirements_alt.txt
echo Starting Smart Attendance Backend...
python app.py
pause
