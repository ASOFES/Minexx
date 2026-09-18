#!/usr/bin/env python
"""
Création d'un superutilisateur admin via variables d'environnement.

Requiert:
  DJANGO_SUPERUSER_USERNAME
  DJANGO_SUPERUSER_PASSWORD
  DJANGO_SUPERUSER_EMAIL (optionnel)
  DJANGO_SUPERUSER_ROLE (défaut: admin)
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.contrib.auth import get_user_model


def create_admin_from_env():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@minexx.com')
    role = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')

    if not username or not password:
        print("Erreur: définir DJANGO_SUPERUSER_USERNAME et DJANGO_SUPERUSER_PASSWORD")
        return False

    User = get_user_model()
    try:
        user = User.objects.get(username=username)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.role = role
        user.email = email
        user.save()
        print(f"Utilisateur '{username}' mis à jour (rôle={role})")
    except User.DoesNotExist:
        user = User.objects.create_superuser(username, email, password)
        user.role = role
        user.save(update_fields=['role'])
        print(f"Utilisateur '{username}' créé (rôle={role})")
    return True


if __name__ == '__main__':
    sys.exit(0 if create_admin_from_env() else 1)
