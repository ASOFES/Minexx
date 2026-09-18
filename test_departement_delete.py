#!/usr/bin/env python
"""
Test des vues de département avec suppression
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.views import departement_delete
from core.models import Etablissement

User = get_user_model()

def test_departement_delete_view():
    """Test de la vue de suppression de département"""
    print("🧪 Test de la vue de suppression de département")
    print("=" * 50)
    
    # Créer un utilisateur admin pour les tests
    try:
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            print("❌ Aucun utilisateur admin trouvé")
            return False
        print(f"✅ Utilisateur admin trouvé: {admin_user.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'utilisateur admin: {e}")
        return False
    
    # Créer un établissement de test
    try:
        import uuid
        code_unique = f"TEST_{uuid.uuid4().hex[:4].upper()}"
        etablissement = Etablissement.objects.create(
            nom=f"Département Test Suppression {code_unique}",
            type="departement",
            code=code_unique,
            actif=True
        )
        print(f"✅ Établissement de test créé: {etablissement.nom} (ID: {etablissement.pk})")
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'établissement de test: {e}")
        return False
    
    # Test de la vue GET (affichage de la confirmation)
    try:
        factory = RequestFactory()
        request = factory.get(f'/departements/{etablissement.pk}/delete/')
        request.user = admin_user
        
        response = departement_delete(request, pk=etablissement.pk)
        print(f"✅ Vue GET - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page de confirmation accessible")
        else:
            print(f"❌ Page de confirmation non accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test GET: {e}")
    
    # Test de la vue POST (suppression)
    try:
        factory = RequestFactory()
        request = factory.post(f'/departements/{etablissement.pk}/delete/')
        request.user = admin_user
        
        response = departement_delete(request, pk=etablissement.pk)
        print(f"✅ Vue POST - Status: {response.status_code}")
        
        # Vérifier que l'établissement a été supprimé
        try:
            Etablissement.objects.get(pk=etablissement.pk)
            print("❌ L'établissement n'a pas été supprimé")
        except Etablissement.DoesNotExist:
            print("✅ L'établissement a été supprimé avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors du test POST: {e}")
    
    print("\n🎯 Test terminé !")
    return True

if __name__ == '__main__':
    test_departement_delete_view()
