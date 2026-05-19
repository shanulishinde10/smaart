@echo off
cd /d "%~dp0backend"
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Smart Attendance Backend...
echo Server will run at http://localhost:5000
echo.
python run.py
pause
