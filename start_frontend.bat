@echo off
cd /d "%~dp0frontend"
echo Starting Smart Attendance Frontend...
echo Server will run at http://localhost:3000
echo.
npx --yes serve . -p 3000
pause
