#!/usr/bin/env python
"""
Script de test pour vérifier que le bouton de création automatique des courses lushi a été supprimé
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_lushi_button_removed():
    """Test pour vérifier que le bouton lushi a été supprimé"""
    print("🧪 Test de suppression du bouton lushi")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test admin
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_admin_lushi',
            defaults={
                'is_staff': True, 
                'is_superuser': True,
                'role': 'admin'
            }
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL du dashboard demandeur
        print("✅ Test de l'URL /demandeur/dashboard/")
        response = client.get('/demandeur/dashboard/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Le dashboard demandeur se charge correctement !")
            
            # Vérifier que le bouton lushi n'est pas présent
            content = response.content.decode('utf-8')
            
            # Vérifications pour s'assurer que le bouton a été supprimé
            lushi_indicators = [
                'creer_courses_lushi',
                'Créer les courses Lushi du jour',
                'fa-bus fa-bounce',
                'lushi-spinner'
            ]
            
            found_indicators = []
            for indicator in lushi_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            if not found_indicators:
                print("✅ Le bouton de création automatique des courses lushi a été supprimé avec succès !")
                print("✅ Aucune référence au bouton lushi trouvée dans le template")
                return True
            else:
                print(f"❌ Le bouton lushi est encore présent. Indicateurs trouvés: {found_indicators}")
                return False
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_lushi_url_removed():
    """Test pour vérifier que l'URL lushi a été supprimée"""
    print("\n🧪 Test de suppression de l'URL lushi")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test admin
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_admin_lushi_url',
            defaults={
                'is_staff': True, 
                'is_superuser': True,
                'role': 'admin'
            }
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL de création des courses lushi (doit retourner 404)
        print("✅ Test de l'URL /demandeur/creer-courses-lushi/")
        response = client.post('/demandeur/creer-courses-lushi/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ L'URL de création des courses lushi a été supprimée avec succès !")
            print("✅ L'URL retourne bien une erreur 404 (page non trouvée)")
            return True
        else:
            print(f"❌ L'URL existe encore. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_lushi_function_removed():
    """Test pour vérifier que la fonction lushi a été supprimée"""
    print("\n🧪 Test de suppression de la fonction lushi")
    print("=" * 50)
    
    try:
        # Tenter d'importer la fonction (doit échouer)
        from core.views import creer_courses_lushi_view
        print("❌ La fonction creer_courses_lushi_view existe encore dans core.views")
        return False
    except ImportError:
        print("✅ La fonction creer_courses_lushi_view a été supprimée avec succès !")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de suppression du bouton lushi")
    print("=" * 60)
    
    tests = [
        test_lushi_button_removed,
        test_lushi_url_removed,
        test_lushi_function_removed
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
        print("🎉 Le bouton de création automatique des courses lushi a été supprimé avec succès !")
        print("✅ Toutes les références ont été supprimées")
        print("✅ L'URL et la fonction ont été supprimées")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 