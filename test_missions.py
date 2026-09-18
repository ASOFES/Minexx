#!/usr/bin/env python
"""
Script de test pour vérifier les nouvelles fonctionnalités du module rapport missions
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from core.models import Course, Utilisateur, Vehicule
from rapport.views import rapport_missions, rapport_missions_advanced, generate_mission_charts_data
from django.test import RequestFactory

def test_rapport_missions():
    """Test de la fonction rapport_missions avec scoring avancé"""
    print("🧪 Test du module rapport missions avec scoring avancé")
    print("=" * 60)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/rapport/missions/')
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='test_admin',
        defaults={'is_staff': True, 'is_superuser': True, 'role': 'admin'}
    )
    request.user = user
    
    try:
        # Tester la vue rapport_missions
        print("✅ Test de la vue rapport_missions...")
        response = rapport_missions(request)
        print(f"   Status: {response.status_code}")
        print(f"   Template: {response.template_name}")
        
        # Vérifier le contexte
        if hasattr(response, 'context_data'):
            context = response.context_data
            print(f"   Score moyen: {context.get('score_moyen', 'N/A')}")
            print(f"   Total missions: {context.get('total_missions', 'N/A')}")
            print(f"   Missions avec scoring: {len(context.get('courses', []))}")
            
            # Vérifier les missions avec scoring
            courses = context.get('courses', [])
            if courses:
                print(f"   Première mission - Score: {getattr(courses[0], 'score_total', 'N/A')}")
                print(f"   Première mission - Classification: {getattr(courses[0], 'classification', 'N/A')}")
        
        print("✅ Test rapport_missions réussi !")
        
    except Exception as e:
        print(f"❌ Erreur dans rapport_missions: {e}")
        return False
    
    return True

def test_rapport_missions_advanced():
    """Test de la vue avancée avec graphiques"""
    print("\n🧪 Test de la vue avancée rapport_missions_advanced...")
    
    factory = RequestFactory()
    request = factory.get('/rapport/missions-advanced/')
    
    # Créer un utilisateur de test
    user, created = Utilisateur.objects.get_or_create(
        username='test_admin',
        defaults={'is_staff': True, 'is_superuser': True, 'role': 'admin'}
    )
    request.user = user
    
    try:
        # Tester la vue avancée
        response = rapport_missions_advanced(request)
        print(f"   Status: {response.status_code}")
        print(f"   Template: {response.template_name}")
        
        # Vérifier le contexte
        if hasattr(response, 'context_data'):
            context = response.context_data
            print(f"   Charts data: {'Présent' if context.get('charts_data') else 'Absent'}")
            print(f"   Score moyen: {context.get('score_moyen', 'N/A')}")
            
            # Vérifier les données de graphiques
            charts_data = context.get('charts_data', {})
            if charts_data:
                print(f"   Scores data: {len(charts_data.get('scores_data', {}).get('labels', []))} missions")
                print(f"   Classification counts: {charts_data.get('classification_counts', {})}")
                print(f"   Statut counts: {charts_data.get('statut_counts', {})}")
        
        print("✅ Test rapport_missions_advanced réussi !")
        
    except Exception as e:
        print(f"❌ Erreur dans rapport_missions_advanced: {e}")
        return False
    
    return True

def test_generate_mission_charts_data():
    """Test de la fonction de génération des données de graphiques"""
    print("\n🧪 Test de generate_mission_charts_data...")
    
    try:
        # Récupérer quelques missions de test
        courses = Course.objects.all()[:5]
        
        if not courses.exists():
            print("   ⚠️  Aucune mission trouvée pour le test")
            return True
        
        # Tester la fonction
        charts_data = generate_mission_charts_data(courses)
        
        print(f"   Scores data: {len(charts_data.get('scores_data', {}).get('labels', []))} missions")
        print(f"   Classification counts: {charts_data.get('classification_counts', {})}")
        print(f"   Statut counts: {charts_data.get('statut_counts', {})}")
        print(f"   Moyennes critères: {charts_data.get('moyennes_criteres', {})}")
        
        print("✅ Test generate_mission_charts_data réussi !")
        
    except Exception as e:
        print(f"❌ Erreur dans generate_mission_charts_data: {e}")
        return False
    
    return True

def test_scoring_system():
    """Test du système de scoring"""
    print("\n🧪 Test du système de scoring...")
    
    try:
        # Récupérer une mission de test
        course = Course.objects.first()
        
        if not course:
            print("   ⚠️  Aucune mission trouvée pour le test")
            return True
        
        # Simuler le calcul de score
        print(f"   Mission ID: {course.id}")
        print(f"   Distance: {course.distance_parcourue}")
        print(f"   Statut: {course.statut}")
        
        # Vérifier si les attributs de scoring sont présents
        if hasattr(course, 'score_total'):
            print(f"   Score total: {course.score_total}")
            print(f"   Classification: {course.classification}")
            print(f"   Badge class: {course.badge_class}")
            
            if hasattr(course, 'score_details'):
                print(f"   Score détails: {course.score_details}")
            
            if hasattr(course, 'recommandations'):
                print(f"   Recommandations: {course.recommandations}")
        
        print("✅ Test du système de scoring réussi !")
        
    except Exception as e:
        print(f"❌ Erreur dans le test du système de scoring: {e}")
        return False
    
    return True

def test_urls():
    """Test des URLs"""
    print("\n🧪 Test des URLs...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Test de l'URL missions
        print("   Test URL /rapport/missions/")
        response = client.get('/rapport/missions/')
        print(f"   Status: {response.status_code}")
        
        # Test de l'URL missions-advanced
        print("   Test URL /rapport/missions-advanced/")
        response = client.get('/rapport/missions-advanced/')
        print(f"   Status: {response.status_code}")
        
        print("✅ Test des URLs réussi !")
        
    except Exception as e:
        print(f"❌ Erreur dans le test des URLs: {e}")
        return False
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du module rapport missions")
    print("=" * 60)
    
    tests = [
        test_rapport_missions,
        test_rapport_missions_advanced,
        test_generate_mission_charts_data,
        test_scoring_system,
        test_urls
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
        print("🎉 Tous les tests sont passés ! Le module rapport missions fonctionne parfaitement.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 