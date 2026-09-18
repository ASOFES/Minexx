@echo off
echo Arrêt des processus Python existants...
taskkill /F /IM python.exe /T
timeout /t 2 /nobreak
echo Démarrage du serveur dans une nouvelle fenêtre...
start cmd /k "cd /d %~dp0.. && python manage.py runserver"
echo Le serveur a été redémarré ! 