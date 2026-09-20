from django.db import models
from core.models import Utilisateur, Vehicule, ActionTraceur
from django.core.exceptions import ValidationError
from django.utils import timezone

def piece_justificative_path(instance, filename):
    """Définit le chemin où seront stockées les pièces justificatives"""
    return f'entretien/{instance.vehicule.id}/{instance.date_entretien.strftime("%Y%m%d")}_{filename}'

def piece_reparation_path(instance, filename):
    return f'reparations/{instance.vehicule_id}/{timezone.now().strftime("%Y%m%d")}_{filename}'


class Entretien(models.Model):
    """Modèle pour les entretiens de véhicules"""
    TYPE_CHOICES = (
        ('ordinaire', 'Entretien ordinaire'),
        ('mecanique', 'Entretien mécanique'),
    )
    type_entretien = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='ordinaire',
        verbose_name="Type d'entretien"
    )
    STATUS_CHOICES = (
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    )
    
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='entretiens')
    garage = models.CharField(max_length=255)
    date_entretien = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planifie')
    motif = models.TextField()
    cout = models.DecimalField(max_digits=10, decimal_places=2)
    kilometrage = models.PositiveIntegerField(default=0, help_text="Kilométrage du véhicule au moment de l'entretien")
    kilometrage_apres = models.PositiveIntegerField(default=0, help_text="Kilométrage du véhicule après l'entretien", verbose_name="Kilométrage après entretien")
    piece_justificative = models.FileField(upload_to=piece_justificative_path, blank=True, null=True, 
                                          help_text="Facture, reçu ou autre document justificatif (PDF, JPG, PNG)")
    createur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='entretiens_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    commentaires = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Entretien {self.vehicule.immatriculation} - {self.date_entretien} - {self.get_statut_display()}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        is_update = not is_new
        if is_update:
            old = type(self).objects.get(pk=self.pk)
            km_fields = [('kilometrage', old.kilometrage, self.kilometrage),
                         ('kilometrage_apres', old.kilometrage_apres, self.kilometrage_apres)]
            for champ, avant, apres in km_fields:
                if avant != apres and apres is not None:
                    from core.models import HistoriqueKilometrage
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.createur,
                        module='entretien',
                        objet_id=self.pk,
                        valeur_avant=avant,
                        valeur_apres=apres,
                        commentaire=f"Modification du {champ} via Entretien #{self.pk}"
                    )
        super().save(*args, **kwargs)
        if is_new:
            for champ, apres in [('kilometrage', self.kilometrage), ('kilometrage_apres', self.kilometrage_apres)]:
                if apres is not None:
                    from core.models import HistoriqueKilometrage
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.createur,
                        module='entretien',
                        objet_id=self.pk,
                        valeur_avant=None,
                        valeur_apres=apres,
                        commentaire=f"Création du {champ} via Entretien #{self.pk}"
                    )
        if self.statut == 'termine' and self.kilometrage_apres is not None:
            self.vehicule.kilometrage_dernier_entretien = self.kilometrage_apres
            if self.vehicule.kilometrage_actuel is None or self.kilometrage_apres > self.vehicule.kilometrage_actuel:
                self.vehicule.kilometrage_actuel = self.kilometrage_apres
            self.vehicule.save(update_fields=["kilometrage_dernier_entretien", "kilometrage_actuel"])
        if is_new:
            ActionTraceur.objects.create(
                utilisateur=self.createur,
                action="Création d'entretien",
                details=f"Véhicule: {self.vehicule.immatriculation}, Date: {self.date_entretien}, Coût: {self.cout}"
            )
        else:
            ActionTraceur.objects.create(
                utilisateur=self.createur,
                action="Modification d'entretien",
                details=f"Véhicule: {self.vehicule.immatriculation}, Date: {self.date_entretien}, Coût: {self.cout}"
            )
    
    @classmethod
    def cout_total_par_vehicule(cls, vehicule):
        from django.db.models import Sum
        return cls.objects.filter(vehicule=vehicule, statut='termine').aggregate(Sum('cout'))['cout__sum'] or 0
    
    @classmethod
    def cout_total_par_periode(cls, date_debut, date_fin):
        from django.db.models import Sum
        return cls.objects.filter(date_entretien__range=[date_debut, date_fin], statut='termine').aggregate(Sum('cout'))['cout__sum'] or 0

    def clean(self):
        if self.vehicule_id:
            dernier_kilometrage = self.vehicule.kilometrage_actuel
            if self.kilometrage is not None and self.kilometrage < dernier_kilometrage:
                 raise ValidationError(f"Le kilométrage ({self.kilometrage}) ne peut pas être inférieur au dernier kilométrage centralisé ({dernier_kilometrage}).")
            if self.kilometrage_apres is not None and self.kilometrage_apres < dernier_kilometrage:
                 raise ValidationError(f"Le kilométrage après entretien ({self.kilometrage_apres}) ne peut pas être inférieur au dernier kilométrage centralisé ({dernier_kilometrage}).")
        super().clean()


class PieceRemplacee(models.Model):
    """Pièce remplacée lors d'un entretien (nom + quantité + prix)."""
    entretien = models.ForeignKey(
        Entretien, on_delete=models.CASCADE, related_name='pieces_remplacees',
    )
    nom = models.CharField(max_length=200, verbose_name="Nom de la pièce")
    reference = models.CharField(max_length=100, blank=True, default='', verbose_name="Référence")
    quantite = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Prix unitaire ($)",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom', 'id']
        verbose_name = 'Pièce remplacée'
        verbose_name_plural = 'Pièces remplacées'

    def __str__(self):
        return f"{self.nom} x{self.quantite} ({self.prix_unitaire} $)"

    @property
    def montant(self):
        return (self.quantite or 0) * (self.prix_unitaire or 0)

    def clean(self):
        if self.quantite is not None and self.quantite < 1:
            raise ValidationError({'quantite': "La quantité doit être au moins 1."})
        if self.prix_unitaire is not None and self.prix_unitaire < 0:
            raise ValidationError({'prix_unitaire': "Le prix ne peut pas être négatif."})
        super().clean()


class ReparationMecanique(models.Model):
    """
    Problème mécanique à régler.
    Flux: signalement + devis provisoire → attente / en réparation → réparé + devis confirmé.
    """
    STATUS_CHOICES = (
        ('en_attente', 'En attente de réparation'),
        ('en_cours', 'En réparation'),
        ('repare', 'Réparé'),
        ('annule', 'Annulé'),
    )

    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='reparations_mecaniques')
    titre = models.CharField(max_length=200, verbose_name="Problème (résumé)")
    description = models.TextField(verbose_name="Description du problème")
    garage = models.CharField(max_length=255, blank=True, default='', verbose_name="Garage / Prestataire")
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')

    devis_provisoire = models.DecimalField(
        max_digits=12, decimal_places=2,
        verbose_name="Devis provisoire ($)",
        help_text="Estimation avant réparation",
    )
    devis_confirme = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        verbose_name="Devis / coût confirmé ($)",
        help_text="Montant réel pour le bilan comptable (requis à la clôture)",
    )

    date_signalement = models.DateField(default=timezone.localdate, verbose_name="Date du signalement")
    date_debut_reparation = models.DateField(null=True, blank=True, verbose_name="Début réparation")
    date_reparation = models.DateField(null=True, blank=True, verbose_name="Date de réparation terminée")

    piece_justificative = models.FileField(
        upload_to=piece_reparation_path, blank=True, null=True,
        verbose_name="Facture / devis confirmé (PDF, JPG)",
    )
    commentaires = models.TextField(blank=True, default='')

    createur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='reparations_creees',
    )
    confirme_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reparations_confirmees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_signalement', '-id']
        verbose_name = 'Réparation mécanique'
        verbose_name_plural = 'Réparations mécaniques'

    def __str__(self):
        return f"{self.vehicule.immatriculation} — {self.titre} ({self.get_statut_display()})"

    @property
    def est_ouverte(self):
        return self.statut in ('en_attente', 'en_cours')

    @property
    def cout_comptable(self):
        if self.statut == 'repare' and self.devis_confirme is not None:
            return self.devis_confirme
        return self.devis_provisoire

    @property
    def ecart_devis(self):
        """Écart confirmé − provisoire (None si pas encore confirmé)."""
        if self.devis_confirme is None or self.devis_provisoire is None:
            return None
        return self.devis_confirme - self.devis_provisoire

    @property
    def total_lignes_devis(self):
        from django.db.models import Sum, F, DecimalField, ExpressionWrapper
        agg = self.lignes_devis.aggregate(
            t=Sum(
                ExpressionWrapper(
                    F('quantite') * F('prix_unitaire'),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )['t']
        return agg or 0

    def recalculer_devis_depuis_lignes(self, champ='provisoire'):
        """Recalcule devis_provisoire ou devis_confirme depuis les lignes du devis."""
        total = self.total_lignes_devis
        if champ == 'confirme':
            self.devis_confirme = total
            self.save(update_fields=['devis_confirme', 'date_modification'])
        else:
            self.devis_provisoire = total
            self.save(update_fields=['devis_provisoire', 'date_modification'])
        return total

    def clean(self):
        if self.statut == 'repare' and self.devis_confirme is None:
            raise ValidationError({'devis_confirme': "Le devis confirmé est obligatoire pour marquer comme réparé."})
        super().clean()

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.statut == 'repare' and not self.date_reparation:
            self.date_reparation = timezone.localdate()
        if self.statut == 'en_cours' and not self.date_debut_reparation:
            self.date_debut_reparation = timezone.localdate()
        super().save(*args, **kwargs)
        if self.createur_id:
            ActionTraceur.objects.create(
                utilisateur=self.createur,
                action="Création réparation mécanique" if is_new else "Modification réparation mécanique",
                details=(
                    f"Véhicule: {self.vehicule.immatriculation}, Problème: {self.titre}, "
                    f"Statut: {self.get_statut_display()}, "
                    f"Devis prov.: {self.devis_provisoire}, Confirmé: {self.devis_confirme or '—'}"
                ),
            )

    @classmethod
    def cout_confirme_par_vehicule(cls, vehicule):
        from django.db.models import Sum
        return (
            cls.objects.filter(vehicule=vehicule, statut='repare')
            .aggregate(Sum('devis_confirme'))['devis_confirme__sum']
            or 0
        )

    @classmethod
    def cout_provisoire_ouvert_par_vehicule(cls, vehicule):
        from django.db.models import Sum
        return (
            cls.objects.filter(vehicule=vehicule, statut__in=['en_attente', 'en_cours'])
            .aggregate(Sum('devis_provisoire'))['devis_provisoire__sum']
            or 0
        )


class LigneDevisReparation(models.Model):
    """
    Ligne de devis liée à un signalement mécanique (pièce, main-d'œuvre, etc.).
    Le total des lignes alimente le devis provisoire / confirmé.
    """
    TYPE_CHOICES = (
        ('piece', 'Pièce'),
        ('main_oeuvre', "Main-d'œuvre"),
        ('frais', 'Frais / divers'),
        ('autre', 'Autre'),
    )

    reparation = models.ForeignKey(
        ReparationMecanique, on_delete=models.CASCADE, related_name='lignes_devis',
    )
    type_ligne = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='piece', verbose_name="Type",
    )
    designation = models.CharField(max_length=255, verbose_name="Désignation")
    reference = models.CharField(max_length=100, blank=True, default='', verbose_name="Référence")
    quantite = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Prix unitaire ($)",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Ligne de devis réparation'
        verbose_name_plural = 'Lignes de devis réparation'

    def __str__(self):
        return f"{self.designation} x{self.quantite}"

    @property
    def montant(self):
        return (self.quantite or 0) * (self.prix_unitaire or 0)

    def clean(self):
        if self.quantite is not None and self.quantite < 1:
            raise ValidationError({'quantite': "La quantité doit être au moins 1."})
        if self.prix_unitaire is not None and self.prix_unitaire < 0:
            raise ValidationError({'prix_unitaire': "Le prix ne peut pas être négatif."})
        super().clean()
