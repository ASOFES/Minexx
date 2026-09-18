#!/usr/bin/env python
"""
Script de test pour vérifier l'importation des véhicules
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from core.models import Vehicule, Etablissement, Utilisateur

def test_vehicles_import():
    """Teste l'importation des véhicules"""
    print("🧪 Test de l'importation des véhicules")
    print("=" * 50)
    
    # Test 1: Vérifier le nombre total de véhicules
    total_vehicles = Vehicule.objects.count()
    print(f"📊 Total véhicules dans la base: {total_vehicles}")
    
    # Test 2: Vérifier les établissements
    etablissements = Etablissement.objects.all()
    print(f"🏢 Établissements créés: {etablissements.count()}")
    for etab in etablissements:
        print(f"  - {etab.nom} (ID: {etab.id})")
    
    # Test 3: Vérifier les véhicules par marque
    marques = Vehicule.objects.values_list('marque', flat=True).distinct()
    print(f"\n🚗 Véhicules par marque:")
    for marque in marques:
        count = Vehicule.objects.filter(marque=marque).count()
        print(f"  - {marque}: {count} véhicule(s)")
    
    # Test 4: Vérifier les véhicules par établissement
    print(f"\n🏢 Véhicules par établissement:")
    for etab in etablissements:
        count = Vehicule.objects.filter(etablissement=etab).count()
        if count > 0:
            print(f"  - {etab.nom}: {count} véhicule(s)")
    
    # Test 5: Vérifier les véhicules avec des dates d'expiration proches
    from datetime import date, timedelta
    today = date.today()
    warning_date = today + timedelta(days=30)
    
    print(f"\n⚠️  Véhicules avec assurance expirant dans 30 jours:")
    vehicles_expiring = Vehicule.objects.filter(
        date_expiration_assurance__lte=warning_date
    ).exclude(date_expiration_assurance__lt=today)
    
    if vehicles_expiring.exists():
        for vehicle in vehicles_expiring:
            days_left = (vehicle.date_expiration_assurance - today).days
            print(f"  - {vehicle.immatriculation} ({vehicle.marque} {vehicle.modele}): {days_left} jours")
    else:
        print("  Aucun véhicule avec assurance expirant dans 30 jours")
    
    # Test 6: Vérifier les véhicules sans plaque
    vehicles_no_plate = Vehicule.objects.filter(immatriculation__startswith='TEMP_')
    print(f"\n🔍 Véhicules sans plaque (ID temporaire): {vehicles_no_plate.count()}")
    for vehicle in vehicles_no_plate:
        print(f"  - {vehicle.immatriculation}: {vehicle.marque} {vehicle.modele}")
    
    # Test 7: Vérifier la cohérence des données
    print(f"\n✅ Vérification de la cohérence:")
    
    # Vérifier les véhicules sans établissement
    vehicles_no_etab = Vehicule.objects.filter(etablissement__isnull=True)
    if vehicles_no_etab.exists():
        print(f"  ❌ {vehicles_no_etab.count()} véhicule(s) sans établissement")
    else:
        print("  ✅ Tous les véhicules ont un établissement")
    
    # Vérifier les véhicules sans créateur
    vehicles_no_creator = Vehicule.objects.filter(createur__isnull=True)
    if vehicles_no_creator.exists():
        print(f"  ❌ {vehicles_no_creator.count()} véhicule(s) sans créateur")
    else:
        print("  ✅ Tous les véhicules ont un créateur")
    
    # Test 8: Afficher quelques exemples de véhicules
    print(f"\n📋 Exemples de véhicules:")
    sample_vehicles = Vehicule.objects.all()[:5]
    for vehicle in sample_vehicles:
        print(f"  - {vehicle.immatriculation}: {vehicle.marque} {vehicle.modele}")
        print(f"    Établissement: {vehicle.etablissement.nom if vehicle.etablissement else 'Aucun'}")
        print(f"    Assurance expire: {vehicle.date_expiration_assurance}")
        print(f"    Contrôle technique expire: {vehicle.date_expiration_controle_technique}")
        print()
    
    print("🎯 Test terminé!")

def test_specific_vehicles():
    """Teste des véhicules spécifiques de l'image"""
    print("\n🎯 Test des véhicules spécifiques de l'image")
    print("=" * 50)
    
    # Vérifier des véhicules spécifiques
    specific_plates = [
        '9133 AQ05',  # TOYOTA PRADO
        '0595 AV05',  # TOYOTA HILUX
        '3425 AT05',  # TOYOTA HILUX
        '5791 AH05',  # MITSUBISHI PAJERO
        '1815 AV05',  # MITSUBISHI FUSO
        '4787 AS05',  # HYUNDAI ELANTRA
        '6690 AB14',  # TATA BUS
        '6901 AB14',  # TATA BUS
        '7528 AB14',  # TOYOTA COASTER
        '9326 AN05'   # TOYOTA HIACE
    ]
    
    found_count = 0
    for plate in specific_plates:
        try:
            vehicle = Vehicule.objects.get(immatriculation=plate)
            print(f"✅ {plate}: {vehicle.marque} {vehicle.modele} - {vehicle.etablissement.nom if vehicle.etablissement else 'Aucun établissement'}")
            found_count += 1
        except Vehicule.DoesNotExist:
            print(f"❌ {plate}: Non trouvé")
    
    print(f"\n📊 Résumé: {found_count}/{len(specific_plates)} véhicules trouvés")

if __name__ == '__main__':
    try:
        test_vehicles_import()
        test_specific_vehicles()
        print("\n🎉 Tous les tests sont terminés!")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
