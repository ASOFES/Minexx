from django.db import models
from core.models import Utilisateur, Vehicule, ActionTraceur
from django.core.exceptions import ValidationError

def piece_justificative_path(instance, filename):
    """Définit le chemin où seront stockées les pièces justificatives"""
    # Format: entretien/vehicule_id/YYYYMMDD_filename
    return f'entretien/{instance.vehicule.id}/{instance.date_entretien.strftime("%Y%m%d")}_{filename}'

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
        # Historique kilométrage — capturer is_new AVANT super().save()
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
        # Création (nouvel entretien)
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
        # Mise à jour du kilométrage véhicule avec le km APRÈS entretien
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
        """Retourne le coût total des entretiens pour un véhicule"""
        from django.db.models import Sum
        return cls.objects.filter(vehicule=vehicule, statut='termine').aggregate(Sum('cout'))['cout__sum'] or 0
    
    @classmethod
    def cout_total_par_periode(cls, date_debut, date_fin):
        """Retourne le coût total des entretiens pour une période donnée"""
        from django.db.models import Sum
        return cls.objects.filter(date_entretien__range=[date_debut, date_fin], statut='termine').aggregate(Sum('cout'))['cout__sum'] or 0

    def clean(self):
        # Vérification du dernier kilométrage connu (centralisé via vehicule.kilometrage_actuel)
        if self.vehicule_id:
            dernier_kilometrage = self.vehicule.kilometrage_actuel
            if self.kilometrage is not None and self.kilometrage < dernier_kilometrage:
                 raise ValidationError(f"Le kilométrage ({self.kilometrage}) ne peut pas être inférieur au dernier kilométrage centralisé ({dernier_kilometrage}).")
            if self.kilometrage_apres is not None and self.kilometrage_apres < dernier_kilometrage:
                 raise ValidationError(f"Le kilométrage après entretien ({self.kilometrage_apres}) ne peut pas être inférieur au dernier kilométrage centralisé ({dernier_kilometrage}).")
        super().clean()
