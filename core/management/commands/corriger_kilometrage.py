from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Course, Vehicule, HistoriqueKilometrage
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les incohérences de kilométrage dans les courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicule',
            type=str,
            help='Immatriculation du véhicule à corriger (optionnel)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les corrections sans les appliquer'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Applique les corrections'
        )

    def handle(self, *args, **options):
        vehicule_immat = options.get('vehicule')
        dry_run = options.get('dry_run')
        fix = options.get('fix')

        if not dry_run and not fix:
            self.stdout.write(
                self.style.WARNING(
                    'Utilisez --dry-run pour voir les corrections ou --fix pour les appliquer'
                )
            )
            return

        # Filtrer les véhicules
        if vehicule_immat:
            vehicules = Vehicule.objects.filter(immatriculation__icontains=vehicule_immat)
        else:
            vehicules = Vehicule.objects.all()

        corrections_appliquees = 0

        for vehicule in vehicules:
            self.stdout.write(f"\n=== Vérification du véhicule {vehicule.immatriculation} ===")
            
            # Récupérer toutes les courses du véhicule
            courses = Course.objects.filter(
                vehicule=vehicule,
                statut='terminee'
            ).order_by('date_fin')

            if not courses.exists():
                self.stdout.write(f"Aucune course terminée pour {vehicule.immatriculation}")
                continue

            # Calculer le kilométrage correct en partant du kilométrage initial
            kilometrage_courant = vehicule.kilometrage_actuel or 0
            courses_corrigees = []

            for course in courses:
                km_depart = course.kilometrage_depart
                km_fin = course.kilometrage_fin
                distance_calculee = km_fin - km_depart if km_fin and km_depart else 0

                # Vérifier si la course a une distance raisonnable (max 1000 km par course)
                if distance_calculee > 1000:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Course #{course.id}: Distance excessive {distance_calculee} km "
                            f"(départ: {km_depart}, fin: {km_fin})"
                        )
                    )
                    
                    # Corriger en utilisant une distance raisonnable
                    nouvelle_distance = min(distance_calculee, 500)  # Max 500 km
                    nouveau_km_fin = km_depart + nouvelle_distance
                    
                    correction = {
                        'course_id': course.id,
                        'ancien_km_fin': km_fin,
                        'nouveau_km_fin': nouveau_km_fin,
                        'ancienne_distance': distance_calculee,
                        'nouvelle_distance': nouvelle_distance
                    }
                    courses_corrigees.append(correction)

                    if fix:
                        with transaction.atomic():
                            # Mettre à jour la course
                            course.kilometrage_fin = nouveau_km_fin
                            course.distance_parcourue = nouvelle_distance
                            course.save()

                            # Créer une entrée dans l'historique
                            HistoriqueKilometrage.objects.create(
                                vehicule=vehicule,
                                utilisateur=course.chauffeur,
                                module='course',
                                objet_id=course.id,
                                valeur_avant=km_fin,
                                valeur_apres=nouveau_km_fin,
                                commentaire=f"Correction automatique - Distance excessive réduite de {distance_calculee} à {nouvelle_distance} km"
                            )

                            corrections_appliquees += 1

                    self.stdout.write(
                        f"  → Correction: {km_fin} → {nouveau_km_fin} km "
                        f"(distance: {distance_calculee} → {nouvelle_distance} km)"
                    )

            # Mettre à jour le kilométrage du véhicule si nécessaire
            if courses_corrigees and fix:
                dernier_km = max(course.kilometrage_fin for course in courses if course.kilometrage_fin)
                if dernier_km > vehicule.kilometrage_actuel:
                    ancien_km_vehicule = vehicule.kilometrage_actuel
                    vehicule.kilometrage_actuel = dernier_km
                    vehicule.save(update_fields=['kilometrage_actuel'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Kilométrage véhicule mis à jour: {ancien_km_vehicule} → {dernier_km} km"
                        )
                    )

        if fix:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ {corrections_appliquees} corrections appliquées avec succès"
                )
            )
        else:
            total_courses = sum(1 for v in vehicules for c in Course.objects.filter(vehicule=v, statut='terminee'))
            self.stdout.write(
                self.style.WARNING(
                    f"\n📋 {total_courses} courses analysées"
                )
            ) 