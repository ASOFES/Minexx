#!/usr/bin/env python3
"""
Script de nettoyage automatique des imports problématiques
pour le déploiement sur Render
"""

import os
import re
from pathlib import Path

# Imports à commenter
PROBLEMATIC_IMPORTS = [
    'import matplotlib.pyplot as plt',
    'from matplotlib import pyplot as plt',
    'import matplotlib',
    'from xhtml2pdf import pisa',
    'from xhtml2pdf import pisa as pisa_pdf',
    'from reportlab.lib.pagesizes import',
    'from reportlab.platypus import',
    'from reportlab.lib.styles import',
    'from reportlab.lib import colors',
    'from reportlab.lib.enums import',
    'import pandas as pd',
    'from PIL import Image',
    'import PIL',
    'from weasyprint import HTML',
]

# Fichiers à traiter
FILES_TO_PROCESS = [
    'core/views.py',
    'core/utils.py',
    'demandeur/views.py',
    'dispatch/utils.py',
    'securite/views.py',
    'ravitaillement/views.py',
    'suivi/views.py',
    'rapport/views.py',
    'notifications/utils.py',
    'chauffeur/views.py',  # Ajouté pour résoudre l'erreur weasyprint
]

def clean_file(file_path):
    """Nettoie un fichier en commentant les imports problématiques"""
    if not os.path.exists(file_path):
        print(f"⚠️  Fichier non trouvé: {file_path}")
        return False
    
    print(f"🧹 Nettoyage de {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Commenter les imports problématiques
    for import_line in PROBLEMATIC_IMPORTS:
        if import_line in content:
            # Trouver toutes les occurrences
            pattern = re.escape(import_line)
            matches = re.finditer(pattern, content)
            
            for match in reversed(list(matches)):
                start, end = match.span()
                # Vérifier si c'est déjà commenté
                line_start = content.rfind('\n', 0, start) + 1
                line_end = content.find('\n', end)
                if line_end == -1:
                    line_end = len(content)
                
                full_line = content[line_start:line_end].strip()
                
                if not full_line.startswith('#'):
                    # Commenter la ligne
                    content = content[:start] + '# ' + content[start:end] + '  # Temporairement commenté pour le déploiement' + content[end:]
                    modified = True
                    print(f"   ✅ Commenté: {full_line[:50]}...")
    
    # Sauvegarder si modifié
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   💾 Fichier sauvegardé")
        return True
    else:
        print(f"   ℹ️  Aucune modification nécessaire")
        return False

def main():
    """Fonction principale"""
    print("🚀 Script de nettoyage des imports problématiques")
    print("=" * 60)
    
    total_modified = 0
    
    for file_path in FILES_TO_PROCESS:
        if clean_file(file_path):
            total_modified += 1
        print()
    
    print("=" * 60)
    print(f"🎉 Nettoyage terminé ! {total_modified} fichiers modifiés")
    print("\n📋 Prochaines étapes:")
    print("1. Commiter les changements: git add .")
    print("2. Pousser vers GitHub: git commit -m 'Fix: Nettoyer tous les imports problématiques'")
    print("3. Déployer sur Render")
    print("4. Une fois stable, réactiver progressivement les fonctionnalités")

if __name__ == "__main__":
    main()
