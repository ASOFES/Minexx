#!/usr/bin/env python
"""
Script de création de l'objet ApplicationControl initial
Résout l'erreur: ApplicationControl matching query does not exist
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from core.models import ApplicationControl

def create_application_control():
    """Crée l'objet ApplicationControl initial s'il n'existe pas"""

    print("🔧 Création de l'objet ApplicationControl initial...")

    try:
        # Vérifier si ApplicationControl existe déjà
        try:
            app_control = ApplicationControl.objects.get()
            print("✅ ApplicationControl existe déjà:")
            print(f"   ID: {app_control.id}")
            print(f"   Application ouverte: {app_control.is_open}")
            print(f"   Début autorisé: {app_control.start_datetime}")
            print(f"   Fin autorisée: {app_control.end_datetime}")
            print(f"   Message: {app_control.message}")
            return True

        except ApplicationControl.DoesNotExist:
            print("👤 Création d'un nouvel objet ApplicationControl...")

            # Créer l'objet ApplicationControl initial avec les bons champs
            app_control = ApplicationControl.objects.create(
                is_open=True,
                start_datetime=django.utils.timezone.now(),
                end_datetime=None,  # Pas de fin définie
                message="L'application est actuellement accessible."
            )

            print("✅ ApplicationControl créé avec succès!")
            print(f"   ID: {app_control.id}")
            print(f"   Application ouverte: {app_control.is_open}")
            print(f"   Début autorisé: {app_control.start_datetime}")
            print(f"   Message: {app_control.message}")

            return True

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    success = create_application_control()
    if success:
        print("\n🚀 ApplicationControl initialisé!")
    else:
        print("\n⚠️ Initialisation échouée.")
