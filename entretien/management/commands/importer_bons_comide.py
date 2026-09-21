from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_date

from core.models import Utilisateur, Vehicule
from entretien.models import LigneDevisReparation, ReparationMecanique

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'bons_comide'

# Bons COMIDE Kisanfu 20/09/2026 — prix indiqués sur le bon (lignes sans prix = 0).
BONS = [
    {
        'cle': 'COMIDE-HILUX-20260920',
        'modele_contains': 'hilux',
        'titre': 'Entretien complet — bon COMIDE (Hilux)',
        'description': (
            "Devis établi d'après le bon COMIDE Kisanfu du 20/09/2026 "
            "(demandé par PATIENT) pour le Hilux MINEX."
        ),
        'garage': 'COMIDE Kisanfu',
        'date': '2026-09-20',
        'commentaires': 'Source : bon atelier COMIDE. Total lignes chiffrées : 527 USD. Main-d\'œuvre non incluse.',
        'image': 'bon_comide_hilux.jpg',
        'lignes': [
            ('piece', 'Filtre à huile', '90915-20003', 1, '10.00'),
            ('piece', 'Décanteur / filtre gasoil', '23390-0L041', 1, '25.00'),
            ('piece', 'Filtre à air', '17801-0C010', 1, '35.00'),
            ('piece', 'Plaquettes de frein (jeu)', '04465-0K240', 1, '120.00'),
            ('piece', 'Segments de frein (jeu)', '04495-0K070', 1, '80.00'),
            ('piece', 'Ampoule H4 12V', '90981-13058', 2, '2.00'),
            ('piece', 'Balais essuie-glace', '85212-0K091', 2, '35.00'),
            ('piece', 'Huile moteur 15W40 TOTAL (10 L)', '15W40', 1, '64.00'),
            ('piece', 'Huile pont 80W90 (20 L)', 'H090', 1, '90.00'),
            ('piece', 'Ampoule 12V 5W21', '12V/5W/21', 2, '2.00'),
            ('piece', 'Filtre A/C habitacle', '87139-50100', 1, '25.00'),
        ],
    },
    {
        'cle': 'COMIDE-LC-20260920',
        'modele_contains': 'cruiser',
        'titre': 'Entretien complet — bon COMIDE (Land Cruiser)',
        'description': (
            "Devis établi d'après le bon COMIDE Kisanfu du 20/09/2026 "
            "(demandé par PATIENT) pour le Land Cruiser MINEX."
        ),
        'garage': 'COMIDE Kisanfu',
        'date': '2026-09-20',
        'commentaires': (
            "Source : bon atelier COMIDE. Total lignes chiffrées : 466 USD. "
            "Prix à confirmer : courroie A/C, courroies alternateur ×2, ATF Dexron 5 L. "
            "Main-d'œuvre non incluse."
        ),
        'image': 'bon_comide_land_cruiser.jpg',
        'lignes': [
            ('piece', 'Filtre à huile', '90915-30002', 1, '10.00'),
            ('piece', 'Filtre à gasoil', '23390-51070', 1, '25.00'),
            ('piece', 'Filtre à air', '17801-61030', 1, '35.00'),
            ('piece', 'Courroie A/C (prix à confirmer)', '99332-11260', 1, '0.00'),
            ('piece', 'Courroie alternateur (prix à confirmer)', '90916-02452', 2, '0.00'),
            ('piece', 'Plaquettes de frein (jeu)', '04465-60370', 1, '120.00'),
            ('piece', 'Segments de frein (jeu)', '04495-60070', 1, '80.00'),
            ('piece', 'Huile moteur 15W40 TOTAL (15 L)', '15W40', 1, '64.00'),
            ('piece', 'Huile pont 80W90 (20 L)', 'H090', 1, '90.00'),
            ('piece', 'Graisse Q8', 'Q8', 5, '5.00'),
            ('piece', 'Huile de frein DOT 4', 'DOT4', 1, '17.00'),
            ('piece', 'ATF Dexron / rouge 5 L (prix à confirmer)', 'ATF', 1, '0.00'),
        ],
    },
]


class Command(BaseCommand):
    help = "Importe les bons COMIDE Hilux et Land Cruiser comme devis (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recrée les devis même s’ils existent déjà.')

    def handle(self, *args, **options):
        force = options['force']
        user = (
            Utilisateur.objects.filter(is_superuser=True).first()
            or Utilisateur.objects.filter(role='admin').first()
            or Utilisateur.objects.first()
        )
        created = 0
        skipped = 0
        for spec in BONS:
            vehicule = self._trouver_vehicule(spec['modele_contains'])
            if not vehicule:
                self.stderr.write(self.style.WARNING(
                    f"Véhicule '{spec['modele_contains']}' introuvable — devis non créé ({spec['cle']})."
                ))
                skipped += 1
                continue
            existant = ReparationMecanique.objects.filter(
                vehicule=vehicule,
                garage='COMIDE Kisanfu',
                titre=spec['titre'],
                date_signalement=parse_date(spec['date']),
            ).first()
            if existant and not force:
                self.stdout.write(f"Déjà présent : {existant} (#{existant.pk})")
                skipped += 1
                continue
            with transaction.atomic():
                if existant and force:
                    existant.lignes_devis.all().delete()
                    existant.delete()
                reparation = ReparationMecanique(
                    vehicule=vehicule,
                    titre=spec['titre'],
                    description=spec['description'],
                    garage=spec['garage'],
                    statut='en_attente',
                    devis_provisoire=Decimal('0'),
                    date_signalement=parse_date(spec['date']),
                    commentaires=spec['commentaires'],
                    createur=user,
                    numero_dossier=spec['cle'],
                )
                image_path = DATA_DIR / spec['image']
                if image_path.is_file():
                    with image_path.open('rb') as fh:
                        reparation.bon_garage.save(spec['image'], File(fh), save=False)
                reparation.save()
                for type_ligne, designation, reference, qte, pu in spec['lignes']:
                    LigneDevisReparation.objects.create(
                        reparation=reparation,
                        type_ligne=type_ligne,
                        designation=designation,
                        reference=reference,
                        quantite=qte,
                        prix_unitaire=Decimal(pu),
                    )
                total = reparation.recalculer_devis_depuis_lignes(champ='provisoire')
                created += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Cree {spec['cle']} - {vehicule.immatriculation} - devis {total} $ (#{reparation.pk})"
                ))
        self.stdout.write(f"Termine. Crees: {created}, ignores: {skipped}.")

    def _trouver_vehicule(self, needle):
        qs = Vehicule.objects.filter(modele__icontains=needle)
        if qs.count() == 1:
            return qs.first()
        blanc = qs.filter(couleur__icontains='blanc')
        if blanc.exists():
            return blanc.first()
        if qs.exists():
            return qs.first()
        return Vehicule.objects.filter(marque__icontains='toyota', modele__icontains=needle).first()
