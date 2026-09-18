"""Réinitialise le mot de passe d'un utilisateur via variables d'environnement.

Requiert:
  RESET_USERNAME
  RESET_PASSWORD
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('RESET_USERNAME')
password = os.environ.get('RESET_PASSWORD')

if not username or not password:
    print("Erreur: définir RESET_USERNAME et RESET_PASSWORD")
    sys.exit(1)

user, created = User.objects.get_or_create(username=username)
user.set_password(password)
user.is_active = True
user.save()

if created:
    print(f"Utilisateur '{username}' créé et mot de passe défini.")
else:
    print(f"Mot de passe de '{username}' réinitialisé.")
