from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
from core.models import Utilisateur, ActionTraceur, Etablissement


class Rapport(models.Model):
    """Modèle pour les rapports générés"""
    TYPE_CHOICES = (
        ('course', 'Rapport de courses'),
        ('vehicule', 'Rapport de véhicule'),
        ('chauffeur', 'Rapport de chauffeur'),
        ('entretien', 'Rapport d\'entretien'),
        ('ravitaillement', 'Rapport de ravitaillement'),
        ('general', 'Rapport général'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )
    
    titre = models.CharField(max_length=255)
    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES)
    format_rapport = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_generation = models.DateTimeField(auto_now_add=True)
    generateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='rapports_generes')
    fichier = models.FileField(upload_to='rapports/', blank=True, null=True)
    parametres = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.titre} - {self.date_generation}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            ActionTraceur.objects.create(
                utilisateur=self.generateur,
                action="Génération de rapport",
                details=f"Type: {self.get_type_rapport_display()}, Période: {self.date_debut} - {self.date_fin}"
            )


class BudgetFlotte(models.Model):
    """
    Budget prévisionnel mensuel ou annuel pour le charroi (flotte).
    Comparé aux dépenses réelles : carburant + entretiens + réparations confirmées.
    """
    PERIODE_MENSUEL = 'mensuel'
    PERIODE_ANNUEL = 'annuel'
    PERIODE_CHOICES = (
        (PERIODE_MENSUEL, 'Mensuel'),
        (PERIODE_ANNUEL, 'Annuel'),
    )
    MOIS_CHOICES = (
        (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
        (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
        (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre'),
    )

    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.CASCADE, null=True, blank=True,
        related_name='budgets_flotte',
        verbose_name="Département (vide = flotte globale)",
    )
    periode_type = models.CharField(max_length=10, choices=PERIODE_CHOICES, default=PERIODE_MENSUEL)
    annee = models.PositiveIntegerField(verbose_name="Année")
    mois = models.PositiveSmallIntegerField(
        choices=MOIS_CHOICES, null=True, blank=True,
        verbose_name="Mois (si mensuel)",
    )

    budget_carburant = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    budget_entretien = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    budget_reparations = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0'))
    budget_documents_bord = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Budget achat documents de bord ($)",
        help_text="Assurance, vignette, carte rose, contrôle technique, stationnement, etc.",
    )
    budget_divers = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
        verbose_name="Divers / imprévus ($)",
    )

    notes = models.TextField(blank=True, default='')
    createur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='budgets_crees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-annee', '-mois', 'periode_type']
        verbose_name = 'Budget flotte'
        verbose_name_plural = 'Budgets flotte'
        constraints = [
            models.UniqueConstraint(
                fields=['etablissement', 'periode_type', 'annee', 'mois'],
                name='uniq_budget_flotte_periode',
            ),
        ]

    def __str__(self):
        scope = self.etablissement.nom if self.etablissement_id else 'Flotte globale'
        if self.periode_type == self.PERIODE_ANNUEL:
            return f"Budget annuel {self.annee} — {scope}"
        mois_label = dict(self.MOIS_CHOICES).get(self.mois, self.mois)
        return f"Budget {mois_label} {self.annee} — {scope}"

    @property
    def budget_total(self):
        return (
            (self.budget_carburant or 0)
            + (self.budget_entretien or 0)
            + (self.budget_reparations or 0)
            + (self.budget_documents_bord or 0)
            + (self.budget_divers or 0)
        )

    def clean(self):
        if self.periode_type == self.PERIODE_MENSUEL and not self.mois:
            raise ValidationError({'mois': 'Le mois est obligatoire pour un budget mensuel.'})
        if self.periode_type == self.PERIODE_ANNUEL:
            self.mois = None
        if self.annee and (self.annee < 2000 or self.annee > 2100):
            raise ValidationError({'annee': 'Année invalide.'})
        super().clean()

    def periode_dates(self):
        """Retourne (date_debut, date_fin) inclusives pour calculer les dépenses réelles."""
        import calendar
        from datetime import date
        if self.periode_type == self.PERIODE_ANNUEL:
            return date(self.annee, 1, 1), date(self.annee, 12, 31)
        last = calendar.monthrange(self.annee, self.mois)[1]
        return date(self.annee, self.mois, 1), date(self.annee, self.mois, last)

    def depenses_reelles(self):
        """Agrège carburant + entretiens + réparations + documents de bord sur la période."""
        from ravitaillement.models import Ravitaillement
        from entretien.models import Entretien, ReparationMecanique

        debut, fin = self.periode_dates()
        ravs = Ravitaillement.objects.filter(
            date_ravitaillement__date__gte=debut,
            date_ravitaillement__date__lte=fin,
        )
        ents = Entretien.objects.filter(
            statut='termine',
            date_entretien__gte=debut,
            date_entretien__lte=fin,
        )
        reps = ReparationMecanique.objects.filter(
            statut='repare',
            devis_confirme__isnull=False,
        ).annotate(
            date_comptable=Coalesce('date_reparation', 'date_signalement')
        ).filter(date_comptable__gte=debut, date_comptable__lte=fin)
        docs = AchatDocumentBord.objects.filter(
            date_achat__gte=debut,
            date_achat__lte=fin,
        )

        if self.etablissement_id:
            ravs = ravs.filter(vehicule__etablissement=self.etablissement)
            ents = ents.filter(vehicule__etablissement=self.etablissement)
            reps = reps.filter(vehicule__etablissement=self.etablissement)
            docs = docs.filter(
                models.Q(vehicule__etablissement=self.etablissement)
                | models.Q(etablissement=self.etablissement)
            )

        carburant = ravs.aggregate(t=Coalesce(Sum('cout_total'), Decimal('0')))['t']
        entretien = ents.aggregate(t=Coalesce(Sum('cout'), Decimal('0')))['t']
        reparations = reps.aggregate(t=Coalesce(Sum('devis_confirme'), Decimal('0')))['t']
        documents = docs.aggregate(t=Coalesce(Sum('montant'), Decimal('0')))['t']
        total = carburant + entretien + reparations + documents
        return {
            'carburant': carburant,
            'entretien': entretien,
            'reparations': reparations,
            'documents_bord': documents,
            'total': total,
        }

    def suivi(self):
        """Budget vs réel + écarts et % consommation."""
        reel = self.depenses_reelles()
        budg_c = self.budget_carburant or Decimal('0')
        budg_e = self.budget_entretien or Decimal('0')
        budg_r = self.budget_reparations or Decimal('0')
        budg_d = self.budget_documents_bord or Decimal('0')
        budg_t = self.budget_total

        def pct(spent, budget):
            if not budget or budget <= 0:
                return None
            return float((spent / budget) * 100)

        return {
            'reel': reel,
            'budget_total': budg_t,
            'ecart_total': budg_t - reel['total'],
            'pct_total': pct(reel['total'], budg_t),
            'pct_carburant': pct(reel['carburant'], budg_c),
            'pct_entretien': pct(reel['entretien'], budg_e),
            'pct_reparations': pct(reel['reparations'], budg_r),
            'pct_documents_bord': pct(reel['documents_bord'], budg_d),
            'ecart_carburant': budg_c - reel['carburant'],
            'ecart_entretien': budg_e - reel['entretien'],
            'ecart_reparations': budg_r - reel['reparations'],
            'ecart_documents_bord': budg_d - reel['documents_bord'],
        }


class AchatDocumentBord(models.Model):
    """Achat / renouvellement de documents de bord d'un véhicule."""
    TYPE_CHOICES = (
        ('assurance', 'Assurance'),
        ('vignette', 'Vignette'),
        ('carte_rose', 'Carte rose'),
        ('controle_technique', 'Contrôle technique'),
        ('stationnement', 'Autorisation de stationnement'),
        ('autre', 'Autre document de bord'),
    )

    vehicule = models.ForeignKey(
        'core.Vehicule', on_delete=models.CASCADE,
        related_name='achats_documents_bord',
    )
    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='achats_documents_bord',
    )
    type_document = models.CharField(max_length=30, choices=TYPE_CHOICES)
    libelle = models.CharField(
        max_length=200, blank=True, default='',
        help_text="Précision optionnelle (ex. assureur, n° quittance)",
    )
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    date_achat = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    piece_jointe = models.FileField(
        upload_to='documents_bord/achats/', blank=True, null=True,
    )
    notes = models.TextField(blank=True, default='')
    createur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='achats_documents_bord',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_achat', '-id']
        verbose_name = 'Achat document de bord'
        verbose_name_plural = 'Achats documents de bord'

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.vehicule.immatriculation} ({self.montant} $)"

    def save(self, *args, **kwargs):
        if self.vehicule_id and not self.etablissement_id:
            self.etablissement_id = self.vehicule.etablissement_id
        super().save(*args, **kwargs)
