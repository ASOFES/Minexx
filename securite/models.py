from django.db import models
from django.utils import timezone
from core.models import Utilisateur, Vehicule, ActionTraceur
from django.core.exceptions import ValidationError

class CheckListSecurite(models.Model):
    """Modèle pour la check-list de sécurité avant et après course"""
    # Le champ type_check a été supprimé dans la migration 0002_update_checklistsecurite.py
    
    STATUT_CHOICES = (
        ('conforme', 'Conforme'),
        ('anomalie_mineure', 'Anomalie mineure'),
        ('non_conforme', 'Non conforme'),
    )
    
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='check_lists')
    controleur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='check_lists_effectuees')
    # Champs ajoutés dans la migration 0002
    date_controle = models.DateTimeField(default=timezone.now)
    lieu_controle = models.CharField(max_length=100)
    
    # Nouveaux champs ajoutés dans la migration 0002
    # Statut global de la checklist
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='conforme')
    
    # Éléments de la check-list avec des choix
    phares_avant = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('defectueux', 'Défectueux')
    ], default='ok')
    
    phares_arriere = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('defectueux', 'Défectueux')
    ], default='ok')
    
    clignotants = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('defectueux', 'Défectueux')
    ], default='ok')
    
    etat_pneus = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('usure', 'Usure'), 
        ('critique', 'Critique')
    ], default='ok')
    
    carrosserie = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('rayures', 'Rayures mineures'), 
        ('dommages', 'Dommages importants')
    ], default='ok')
    
    tableau_bord = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('voyants', 'Voyants allumés')
    ], default='ok')
    
    freins = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('usure', 'Usure'), 
        ('defectueux', 'Défectueux')
    ], default='ok')
    
    ceintures = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('defectueuses', 'Défectueuses')
    ], default='ok')
    
    proprete = models.CharField(max_length=20, choices=[
        ('ok', 'OK'), 
        ('sale', 'Sale')
    ], default='ok')
    
    carte_grise = models.CharField(max_length=20, choices=[
        ('present', 'Présente'), 
        ('absent', 'Absente')
    ], default='present')
    
    assurance = models.CharField(max_length=20, choices=[
        ('present', 'Présente'), 
        ('absent', 'Absente')
    ], default='present')
    
    triangle = models.CharField(max_length=20, choices=[
        ('present', 'Présent'), 
        ('absent', 'Absent')
    ], default='present')
    
    type_check = models.CharField(
    max_length=10,
    choices=[('depart', 'Avant course'), ('retour', 'Après course')],
    default='depart',
    verbose_name='Type de check-list'
)

# Kilométrage
    kilometrage = models.PositiveIntegerField()
    
    # Commentaires
    commentaires = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Check-list {self.vehicule.immatriculation} - {self.date_controle}"
    
    def clean(self):
        # Vérification du dernier kilométrage connu (centralisé via vehicule.kilometrage_actuel)
        if self.vehicule_id:
            dernier_kilometrage = self.vehicule.kilometrage_actuel
            if dernier_kilometrage is not None and self.kilometrage is not None and self.kilometrage < dernier_kilometrage:
                raise ValidationError(f"Le kilométrage ({self.kilometrage}) ne peut pas être inférieur au dernier kilométrage centralisé ({dernier_kilometrage}).")
        super().clean()

    def save(self, *args, **kwargs):
        # Créer une entrée dans le traceur d'actions
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            action = f"Check-list effectuée pour le véhicule {self.vehicule.immatriculation}"
            ActionTraceur.objects.create(
                utilisateur=self.controleur,
                action=action,
                details=f"Kilométrage: {self.kilometrage}, Statut: {self.statut}"
            )
            # Le km centralisé ne peut que progresser (pas de retour en arrière via checklist)
            km_actuel = self.vehicule.kilometrage_actuel
            if self.kilometrage is not None and (km_actuel is None or self.kilometrage > km_actuel):
                self.vehicule.kilometrage_actuel = self.kilometrage
                self.vehicule.save(update_fields=["kilometrage_actuel"])

def incident_photo_path(instance, filename):
    dossier = getattr(instance.incident, 'numero_dossier', None) or instance.incident_id or 'tmp'
    return f'incidents_securite/{dossier}/{filename}'


class IncidentSecurite(models.Model):
    """
    Rapport d'incident / accident.
    Le numero_dossier relie le suivi vers devis et réparations mécaniques.
    """
    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('en_cours', 'En traitement'),
        ('traite', 'Traité'),
        ('clos', 'Clos'),
    ]

    numero_dossier = models.CharField(
        max_length=32, unique=True, blank=True, db_index=True,
        verbose_name="N° de dossier",
        help_text="Référence unique partagée avec devis / réparations",
    )
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='incidents_securite')
    agent = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='incidents_signales')
    date_signalement = models.DateTimeField(default=timezone.now)
    type_incident = models.CharField(max_length=50, choices=[
        ('panne', 'Panne'),
        ('accident', 'Accident'),
        ('defaut_grave', 'Défaut grave'),
        ('autre', 'Autre'),
    ], default='autre')
    description = models.TextField()
    photo = models.ImageField(
        upload_to='incidents_securite/', blank=True, null=True,
        help_text="Photo principale (compatibilité). Préférer les pièces jointes multiples.",
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ouvert')
    commentaires = models.TextField(blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateTimeField(null=True, blank=True)
    traite_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incidents_traites',
    )
    clos_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='incidents_clos',
    )

    class Meta:
        ordering = ['-date_signalement', '-id']
        verbose_name = "Incident sécurité"
        verbose_name_plural = "Incidents sécurité"

    def __str__(self):
        ref = self.numero_dossier or f'#{self.pk}'
        return f"{ref} — {self.get_type_incident_display()} — {self.vehicule.immatriculation}"

    @staticmethod
    def generer_numero_dossier():
        """Génère un n° du type INC-20260920-0001."""
        today = timezone.localdate().strftime('%Y%m%d')
        prefix = f'INC-{today}-'
        last = (
            IncidentSecurite.objects
            .filter(numero_dossier__startswith=prefix)
            .order_by('-numero_dossier')
            .values_list('numero_dossier', flat=True)
            .first()
        )
        seq = 1
        if last:
            try:
                seq = int(str(last).rsplit('-', 1)[-1]) + 1
            except (TypeError, ValueError):
                seq = IncidentSecurite.objects.filter(numero_dossier__startswith=prefix).count() + 1
        return f'{prefix}{seq:04d}'

    @property
    def est_actif(self):
        """Incident encore bloquant pour le véhicule."""
        return self.statut in ('ouvert', 'en_cours')

    def synchroniser_statut_depuis_reparations(self):
        """
        Aligne le statut du dossier sur les réparations / devis liés.
        - réparation ouverte → en_cours
        - toutes réparées (aucune ouverte) → traite
        - ne réouvre jamais un dossier clos
        """
        if self.statut == 'clos':
            return False
        reparations = self.reparations.all()
        if not reparations.exists():
            return False
        ouvertes = reparations.filter(statut__in=['en_attente', 'en_cours']).exists()
        terminees = reparations.filter(statut='repare').exists()
        nouveau = None
        if ouvertes and self.statut in ('ouvert', 'traite'):
            nouveau = 'en_cours'
        elif terminees and not ouvertes and self.statut in ('ouvert', 'en_cours'):
            nouveau = 'traite'
        if nouveau and nouveau != self.statut:
            self.statut = nouveau
            update_fields = ['statut', 'date_modification']
            if nouveau == 'traite' and not self.date_traitement:
                self.date_traitement = timezone.now()
                update_fields.append('date_traitement')
            self.save(update_fields=update_fields)
            return True
        return False

    def marquer_traite(self, utilisateur=None):
        if self.statut == 'clos':
            return False
        self.statut = 'traite'
        self.date_traitement = timezone.now()
        if utilisateur:
            self.traite_par = utilisateur
        self.save(update_fields=['statut', 'date_traitement', 'traite_par', 'date_modification'])
        return True

    def cloturer(self, utilisateur=None):
        self.statut = 'clos'
        self.date_cloture = timezone.now()
        if utilisateur:
            self.clos_par = utilisateur
        if not self.date_traitement:
            self.date_traitement = self.date_cloture
        self.save(update_fields=[
            'statut', 'date_cloture', 'clos_par', 'date_traitement', 'date_modification',
        ])
        return True

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            # Garantir l'unicité même en création concurrente légère
            for _ in range(5):
                candidate = self.generer_numero_dossier()
                if not IncidentSecurite.objects.filter(numero_dossier=candidate).exists():
                    self.numero_dossier = candidate
                    break
            else:
                self.numero_dossier = f"INC-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.vehicule_id or 0}"
        super().save(*args, **kwargs)


class PhotoIncidentSecurite(models.Model):
    """Pièces jointes images d'un rapport d'incident (plusieurs autorisées)."""
    incident = models.ForeignKey(
        IncidentSecurite, on_delete=models.CASCADE, related_name='photos',
    )
    image = models.ImageField(upload_to=incident_photo_path, verbose_name="Image")
    legende = models.CharField(max_length=255, blank=True, default='')
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_ajout', 'id']
        verbose_name = "Photo d'incident"
        verbose_name_plural = "Photos d'incident"

    def __str__(self):
        return f"Photo {self.pk} — {self.incident.numero_dossier}"
