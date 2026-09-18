#!/usr/bin/env python
"""Création d'un superutilisateur via variables d'environnement."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@asofes.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
role = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')

if not password:
    print("Erreur: définir DJANGO_SUPERUSER_PASSWORD")
    sys.exit(1)

if not User.objects.filter(username=username).exists():
    print(f"Création du superutilisateur {username}...")
    user = User.objects.create_superuser(username, email, password)
    if hasattr(user, 'role'):
        user.role = role
        user.save(update_fields=['role'])
    print(f"Superutilisateur {username} créé avec succès!")
else:
    print(f"Un utilisateur avec le nom {username} existe déjà.")
