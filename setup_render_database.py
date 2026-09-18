#!/usr/bin/env python
"""
Script pour configurer la base de données sur Render
Exécute les migrations et crée les objets nécessaires
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from core.models import ApplicationControl, Etablissement

def run_migrations():
    """Exécute les migrations Django"""
    print("🔄 Exécution des migrations...")
    try:
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations exécutées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        return False
    return True

def create_default_etablissement():
    """Crée un établissement par défaut"""
    print("🏢 Création d'un établissement par défaut...")
    try:
        if Etablissement.objects.count() == 0:
            etablissement = Etablissement.objects.create(
                nom="Établissement Principal"
            )
            print(f"✅ Établissement créé: {etablissement}")
        else:
            print("✅ Établissement déjà existant")
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'établissement: {e}")

def create_application_control():
    """Crée l'objet ApplicationControl"""
    print("🔐 Création de l'ApplicationControl...")
    try:
        if ApplicationControl.objects.count() == 0:
            control = ApplicationControl.objects.create(
                is_open=True,
                start_datetime=django.utils.timezone.now(),
                end_datetime=django.utils.timezone.now() + django.utils.timezone.timedelta(days=365),
                message="Application ouverte par défaut"
            )
            print(f"✅ ApplicationControl créé: {control}")
        else:
            print("✅ ApplicationControl déjà existant")
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'ApplicationControl: {e}")

def create_superuser():
    """Crée un superutilisateur via variables d'environnement"""
    print("👑 Création d'un superutilisateur...")
    try:
        import os
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        role = os.environ.get('DJANGO_SUPERUSER_ROLE', 'admin')
        if not password:
            print("⚠️ DJANGO_SUPERUSER_PASSWORD non défini — superutilisateur non créé")
            return
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(username, email, password)
            if hasattr(user, 'role'):
                user.role = role
                user.save(update_fields=['role'])
            print(f"✅ Superutilisateur créé: {user.username}")
        else:
            print("✅ Superutilisateur déjà existant")
    except Exception as e:
        print(f"❌ Erreur lors de la création du superutilisateur: {e}")

def main():
    """Fonction principale"""
    print("🚀 Configuration de la base de données sur Render")
    print("=" * 60)
    
    # Exécuter les migrations
    if not run_migrations():
        print("❌ Impossible de continuer sans migrations")
        return
    
    # Créer les objets nécessaires
    create_default_etablissement()
    create_application_control()
    create_superuser()
    
    print("\n🎯 Configuration terminée avec succès!")
    print("🌐 L'application devrait maintenant fonctionner sur Render")

if __name__ == '__main__':
    main()
