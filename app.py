#!/usr/bin/env python
"""
Point d'entrée pour Render - importe l'application Django
"""

import os
import sys

# Ajouter le répertoire du projet au Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')

# Importer l'application Django
from gestion_vehicules.wsgi import application

# Variable 'app' pour Gunicorn
app = application

if __name__ == '__main__':
    # Pour le développement local
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
