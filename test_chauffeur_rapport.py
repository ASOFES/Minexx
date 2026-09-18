#!/usr/bin/env python
"""
Script de test pour vérifier que l'erreur du template chauffeur est corrigée
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_chauffeur_rapport():
    """Test de l'URL chauffeur/rapport/ qui causait l'erreur"""
    print("🧪 Test de l'URL chauffeur/rapport/")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_chauffeur',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL qui causait l'erreur
        print("✅ Test de l'URL /chauffeur/rapport/")
        response = client.get('/chauffeur/rapport/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ L'erreur TemplateSyntaxError est corrigée !")
            print("✅ La page se charge correctement")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            if hasattr(response, 'content'):
                print(f"   Contenu: {response.content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_multiply_filter():
    """Test pour vérifier que les filtres multiply ne sont plus utilisés"""
    print("\n🧪 Test des filtres multiply dans les templates")
    print("=" * 50)
    
    try:
        # Chercher les occurrences de multiply dans les templates
        import os
        template_dir = os.path.join(os.getcwd(), 'chauffeur', 'templates')
        
        multiply_found = False
        
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'multiply' in content:
                            print(f"   ⚠️  Filtre 'multiply' trouvé dans {file_path}")
                            multiply_found = True
        
        if not multiply_found:
            print("✅ Aucun filtre 'multiply' trouvé dans les templates")
            return True
        else:
            print("❌ Des filtres 'multiply' sont encore présents")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de correction de l'erreur TemplateSyntaxError")
    print("=" * 60)
    
    tests = [
        test_chauffeur_rapport,
        test_multiply_filter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Erreur critique dans {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats des tests: {passed}/{total} réussis")
    
    if passed == total:
        print("🎉 L'erreur TemplateSyntaxError est corrigée !")
        print("✅ Le module chauffeur fonctionne correctement")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 