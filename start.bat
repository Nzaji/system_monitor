@echo off
REM Place le .bat dans le dossier Monitor (C:\Users\FANNY\Desktop\Monitor)
cd /d "%~dp0"

echo Lancement de api.py...
start "API" cmd /k python api.py

timeout /t 2 >nul  && echo Lancement de dashboard.py...
start "Dashboard" cmd /k python TabdeBord.py

timeout /t 2 >nul  && echo Lancement de collect.py...
start "Collect" cmd /k python collect.py

echo Tous les scripts ont été démarrés !
pause