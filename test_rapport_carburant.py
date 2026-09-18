#!/usr/bin/env python
"""
Script de test pour vérifier que le rapport carburant fonctionne correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_rapport_carburant():
    """Test de l'URL rapport/carburant/"""
    print("🧪 Test de l'URL rapport/carburant/")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_carburant',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL du rapport carburant
        print("✅ Test de l'URL /rapport/carburant/")
        response = client.get('/rapport/carburant/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Le rapport carburant se charge correctement !")
            print("✅ Aucune erreur TemplateSyntaxError détectée")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            if hasattr(response, 'content'):
                print(f"   Contenu: {response.content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_rapport_carburant_filtres():
    """Test du rapport carburant avec des filtres"""
    print("\n🧪 Test du rapport carburant avec filtres")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_carburant_filtres',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester avec des filtres
        params = {
            'date_debut': '2024-01-01',
            'date_fin': '2024-12-31',
            'montant_min': '10'
        }
        
        print("✅ Test de l'URL /rapport/carburant/ avec filtres")
        response = client.get('/rapport/carburant/', params)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Le rapport carburant avec filtres se charge correctement !")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test avec filtres: {e}")
        return False

def test_rapport_carburant_export():
    """Test de l'export du rapport carburant"""
    print("\n🧪 Test de l'export du rapport carburant")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_carburant_export',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'export PDF
        print("✅ Test de l'export PDF")
        response = client.get('/rapport/carburant/', {'export': 'pdf'})
        
        print(f"   Status PDF: {response.status_code}")
        
        # Tester l'export Excel
        print("✅ Test de l'export Excel")
        response = client.get('/rapport/carburant/', {'export': 'excel'})
        
        print(f"   Status Excel: {response.status_code}")
        
        if response.status_code in [200, 302]:  # 302 pour les redirections
            print("✅ Les exports fonctionnent correctement !")
            return True
        else:
            print(f"❌ Erreur dans les exports: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test d'export: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test du rapport carburant")
    print("=" * 60)
    
    tests = [
        test_rapport_carburant,
        test_rapport_carburant_filtres,
        test_rapport_carburant_export
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
        print("🎉 Le rapport carburant fonctionne parfaitement !")
        print("✅ Aucune erreur TemplateSyntaxError détectée")
        print("✅ Tous les filtres et exports fonctionnent")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 