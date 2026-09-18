#!/usr/bin/env python
"""
Script de diagnostic pour Render
Vérifie l'état de la base de données et identifie les problèmes
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
from django.db.utils import OperationalError

def check_database():
    """Vérifie la connexion à la base de données"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion à la base de données réussie")
            return True
    except OperationalError as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return False

def check_tables():
    """Vérifie l'existence des tables principales"""
    try:
        with connection.cursor() as cursor:
            # Vérifier les tables principales
            tables_to_check = [
                'core_utilisateur',
                'core_vehicule',
                'core_etablissement',
                'core_applicationcontrol',
                'core_course',
                'core_actiontraceur'
            ]
            
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"✅ Table {table}: {count} enregistrements")
                except Exception as e:
                    print(f"❌ Table {table}: {e}")
                    
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des tables: {e}")

def check_migrations():
    """Vérifie l'état des migrations"""
    try:
        print("\n📋 État des migrations:")
        execute_from_command_line(['manage.py', 'showmigrations'])
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des migrations: {e}")

def check_application_control():
    """Vérifie spécifiquement ApplicationControl"""
    try:
        from core.models import ApplicationControl
        
        try:
            control = ApplicationControl.objects.get(pk=1)
            print(f"✅ ApplicationControl trouvé: {control}")
        except ApplicationControl.DoesNotExist:
            print("❌ ApplicationControl n'existe pas (pk=1)")
            print("Création d'un ApplicationControl par défaut...")
            
            # Créer un ApplicationControl par défaut
            control = ApplicationControl.objects.create(
                is_open=True,
                start_datetime=django.utils.timezone.now(),
                end_datetime=django.utils.timezone.now() + django.utils.timezone.timedelta(days=365),
                message="Application ouverte par défaut"
            )
            print(f"✅ ApplicationControl créé avec succès: {control}")
            
    except Exception as e:
        print(f"❌ Erreur avec ApplicationControl: {e}")

def main():
    """Fonction principale"""
    print("🔍 Diagnostic de l'application sur Render")
    print("=" * 50)
    
    # Vérifier la base de données
    if check_database():
        check_tables()
        check_application_control()
        check_migrations()
    else:
        print("❌ Impossible de continuer sans connexion à la base de données")
        return
    
    print("\n🎯 Diagnostic terminé")

if __name__ == '__main__':
    main()
