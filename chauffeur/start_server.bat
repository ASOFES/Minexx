@echo off
:start
cd /d %~dp0
cd ..
echo Démarrage du serveur Django...
python manage.py runserver
echo Le serveur s'est arrêté. Redémarrage dans 5 secondes...
timeout /t 5 /nobreak
goto start 