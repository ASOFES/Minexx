import os
import django
from django.db import connections
from django.apps import apps

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

def check_database():
    print("=== Vérification de la base de données secondaire ===")
    
    # Vérifier la connexion
    try:
        with connections['secondaire'].cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("\nTables dans la base secondaire :")
            for table in tables:
                print(f"- {table[0]}")
                
            # Pour chaque table, afficher le nombre d'enregistrements
            print("\nNombre d'enregistrements par table :")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"- {table[0]}: {count} enregistrements")
                
    except Exception as e:
        print(f"Erreur lors de la vérification de la base de données : {str(e)}")
    
    print("\n=== Vérification du routage des modèles ===")
    for app_config in apps.get_app_configs():
        if app_config.label in ['rapport', 'notifications']:
            print(f"\nModèles dans l'app {app_config.label} :")
            for model in app_config.get_models():
                print(f"- {model.__name__} (base: {model.objects.db})")

if __name__ == '__main__':
    check_database() 