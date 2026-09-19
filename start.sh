#!/bin/bash

echo "🚀 Démarrage de l'application MINEXX..."

# Vérifier les variables d'environnement
echo "📋 Configuration:"
echo "  - SECRET_KEY: ${SECRET_KEY:+définie}"
echo "  - DEBUG: ${DEBUG:-False}"
echo "  - DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-gestion_vehicules.settings}"
echo "  - PORT: ${PORT:-8000}"

# Attendre que la base de données soit prête (pour PostgreSQL)
if [ -n "$DATABASE_URL" ]; then
    echo "⏳ Attente de la base de données PostgreSQL..."
    # Attendre 30 secondes maximum
    for i in {1..30}; do
        if python manage.py check --database default 2>/dev/null; then
            echo "✅ Base de données PostgreSQL prête!"
            break
        fi
        echo "⏳ Tentative $i/30..."
        sleep 1
    done
fi

# Appliquer les migrations
echo "🔄 Application des migrations Django..."
python manage.py migrate --noinput

# Collecter les fichiers statiques si nécessaire
if [ ! -d "staticfiles" ]; then
    echo "📁 Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
fi

# Dossier média pour photos / documents uploadés
# Sur Railway: créer un Volume monté sur /data/media et définir MEDIA_ROOT=/data/media
MEDIA_DIR="${MEDIA_ROOT:-media}"
mkdir -p "$MEDIA_DIR/images_vehicules" \
         "$MEDIA_DIR/documents_vehicules" \
         "$MEDIA_DIR/documents_vehicules/carte_rose" \
         "$MEDIA_DIR/photos_profil" \
         "$MEDIA_DIR/reparations"
echo "📁 MEDIA_ROOT effectif: $MEDIA_DIR"

# Fuseau horaire applicatif (Lubumbashi UTC+2)
export TZ="${TZ:-Africa/Lubumbashi}"

# Créer un superutilisateur uniquement si les variables d'environnement sont fournies
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@minexx.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
role = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')
if username and password:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(username, email, password)
        if hasattr(user, 'role'):
            user.role = role
            user.save(update_fields=['role'])
        print(f'Superutilisateur créé: {username}')
    else:
        print(f'Utilisateur {username} existe déjà')
elif not User.objects.filter(is_superuser=True).exists():
    print('Aucun superutilisateur. Définir DJANGO_SUPERUSER_USERNAME et DJANGO_SUPERUSER_PASSWORD pour en créer un.')
else:
    print('Superutilisateur existe déjà')
"

# Démarrer l'application (utiliser \$PORT fourni par Render/Railway/Heroku)
echo "🚀 Démarrage de Gunicorn..."
exec gunicorn gestion_vehicules.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
