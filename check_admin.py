#!/usr/bin/env python
import os
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

# Importer le modèle utilisateur
from django.contrib.auth import get_user_model
User = get_user_model()

# Afficher des informations sur le serveur
print("=== Informations sur l'application ASOFES ===\n")
print("URL de l'application: https://asofes.onrender.com/")
print("URL de l'administration: https://asofes.onrender.com/admin/")

# Vérifier l'existence des superutilisateurs
superusers = User.objects.filter(is_superuser=True)

if superusers.exists():
    print("\n=== Superutilisateurs existants ===")
    for user in superusers:
        print(f"Nom d'utilisateur: {user.username}")
        print(f"Email: {user.email}")
        print("-----------------------------------")
    print(f"\nNombre total de superutilisateurs: {superusers.count()}")
else:
    print("\nAucun superutilisateur n'existe encore.")
    print("Exécutez le script create_admin.py pour en créer un.")

print("\n=== Instructions ===")
print("1. Pour créer un superutilisateur, exécutez: python create_admin.py")
print("2. Pour accéder à l'administration, visitez: https://asofes.onrender.com/admin/")
print("3. Connectez-vous avec le nom d'utilisateur et mot de passe créés")
