#!/bin/bash

echo "🚀 Déploiement Railway - MINEXX"
echo "=================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Assurez-vous d'être dans le répertoire du projet Django."
    exit 1
fi

echo "✅ Projet Django détecté"

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py migrate

# Créer un superutilisateur si les variables d'environnement sont définies
echo "👤 Création du superutilisateur..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ.get('DJANGO_SUPERUSER_USERNAME')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@minexx.com')
r = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')
if u and p and not User.objects.filter(username=u).exists():
    user = User.objects.create_superuser(u, e, p)
    if hasattr(user, 'role'):
        user.role = r
        user.save(update_fields=['role'])
    print(f'Superutilisateur créé: {u}')
elif not u or not p:
    print('DJANGO_SUPERUSER_USERNAME/PASSWORD non définis — skip')
else:
    print('Utilisateur déjà existant')
"

echo "✅ Déploiement Railway terminé avec succès!"
echo "🌐 Votre application sera disponible sur: https://minexx-production.up.railway.app" 