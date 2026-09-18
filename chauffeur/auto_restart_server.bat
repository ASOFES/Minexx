@echo off
:loop
REM Arrêter tous les serveurs Django existants
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do taskkill /F /PID %%a

echo Démarrage du serveur Django...
start cmd /k "cd /d %~dp0.. && python manage.py runserver"

echo Attente de 10 secondes avant de vérifier si le serveur tourne...
timeout /t 10 /nobreak

echo Vérification si le serveur tourne...
tasklist | findstr /i "python.exe" >nul
if errorlevel 1 (
    echo Le serveur s'est arrêté. Redémarrage...
    goto loop
) else (
    echo Le serveur tourne. Surveillance continue...
    timeout /t 60 /nobreak
    goto loop
) 