from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError

class Etablissement(models.Model):
    TYPE_CHOICES = (
        ('departement', 'Département'),
        ('direction', 'Direction'),
        ('service', 'Service'),
    )
    nom = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='departement')
    code = models.CharField(max_length=10, unique=True, null=True, blank=True, help_text="Code unique du département")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='enfants')
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    responsable = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='departements_diriges')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['type', 'nom']

    def save(self, *args, **kwargs):
        if not self.code:
            # Générer un code unique basé sur le nom
            base_code = ''.join(c for c in self.nom.upper() if c.isalnum())[:3]
            counter = 1
            while Etablissement.objects.filter(code=f"{base_code}{counter}").exists():
                counter += 1
            self.code = f"{base_code}{counter}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.nom}"

    def get_all_enfants(self):
        """Récupère tous les départements enfants récursivement"""
        enfants = list(self.enfants.all())
        for enfant in self.enfants.all():
            enfants.extend(enfant.get_all_enfants())
        return enfants

    def get_all_parents(self):
        """Récupère tous les départements parents"""
        parents = []
        parent = self.parent
        while parent:
            parents.append(parent)
            parent = parent.parent
        return parents

    def get_hierarchie_complete(self):
        """Récupère la hiérarchie complète du département"""
        return self.get_all_parents() + [self] + self.get_all_enfants()

    @classmethod
    def get_departements_utilisateur(cls, utilisateur):
        """Récupère tous les départements auxquels l'utilisateur a accès"""
        if utilisateur.role == 'admin':
            return cls.objects.all()
        return cls.objects.filter(
            models.Q(utilisateurs=utilisateur) |
            models.Q(responsable=utilisateur)
        ).distinct()

class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé avec des rôles spécifiques"""
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('chauffeur', 'Chauffeur'),
        ('securite', 'Sécurité'),
        ('demandeur', 'Demandeur de missions'),
        ('dispatch', 'Dispatcher'),
        ('consultant', 'Consultant'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='demandeur')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='photos_profil/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    etablissement = models.ForeignKey('Etablissement', on_delete=models.CASCADE, null=True, blank=True, related_name='utilisateurs')
    departements_accessibles = models.ManyToManyField('Etablissement', related_name='utilisateurs_autorises', blank=True)

    # Permis de conduire (chauffeurs)
    possede_permis = models.BooleanField(default=False, verbose_name="Possède un permis de conduire")
    numero_permis = models.CharField(max_length=80, blank=True, default='', verbose_name="Numéro de permis")
    photo_permis = models.ImageField(
        upload_to='documents_permis/',
        blank=True,
        null=True,
        verbose_name="Photo / scan du permis",
    )
    date_expiration_permis = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date d'expiration du permis",
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def jours_avant_expiration_permis(self):
        """Nombre de jours avant expiration du permis (None si non renseigné)."""
        if not self.date_expiration_permis:
            return None
        return (self.date_expiration_permis - timezone.now().date()).days

    def get_departements_accessibles(self):
        """Récupère tous les départements auxquels l'utilisateur a accès"""
        if self.role == 'admin':
            return Etablissement.objects.all()
        return self.departements_accessibles.all()

    def peut_acceder_departement(self, departement):
        """Vérifie si l'utilisateur peut accéder à un département spécifique"""
        if self.role == 'admin':
            return True
        return departement in self.get_departements_accessibles()

class Vehicule(models.Model):
    """Modèle pour les véhicules"""
    etablissement = models.ForeignKey('Etablissement', on_delete=models.CASCADE, null=True, blank=True, related_name='vehicules')
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50, blank=True, default='')
    modele = models.CharField(max_length=50, blank=True, default='')
    couleur = models.CharField(max_length=30, blank=True, default='')
    numero_chassis = models.CharField(max_length=50, unique=True, null=True, blank=True)
    numero_moteur = models.CharField(max_length=80, blank=True, default='', verbose_name="Numéro de moteur")
    numero_carte_rose = models.CharField(max_length=80, blank=True, default='', verbose_name="Numéro carte rose")
    document_carte_rose = models.FileField(
        upload_to='documents_vehicules/carte_rose/',
        blank=True,
        null=True,
        verbose_name="Scan / photo carte rose",
    )
    # Identification individuelle des pneus
    numero_pneu_avant_gauche = models.CharField(max_length=60, blank=True, default='', verbose_name="Pneu avant gauche")
    numero_pneu_avant_droit = models.CharField(max_length=60, blank=True, default='', verbose_name="Pneu avant droit")
    numero_pneu_arriere_gauche = models.CharField(max_length=60, blank=True, default='', verbose_name="Pneu arrière gauche")
    numero_pneu_arriere_droit = models.CharField(max_length=60, blank=True, default='', verbose_name="Pneu arrière droit")
    numero_pneu_secours = models.CharField(max_length=60, blank=True, default='', verbose_name="Pneu de secours")
    kilometrage_debut = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Kilométrage de début",
        help_text="Kilométrage à l'enregistrement du véhicule",
    )
    image = models.ImageField(upload_to='images_vehicules/', blank=True, null=True)
    date_immatriculation = models.DateField(null=True, blank=True)
    date_expiration_assurance = models.DateField(null=True, blank=True)
    date_expiration_controle_technique = models.DateField(null=True, blank=True)
    date_expiration_vignette = models.DateField(null=True, blank=True)
    date_expiration_stationnement = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    createur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='vehicules_crees')
    kilometrage_dernier_entretien = models.PositiveIntegerField(default=0, help_text="Kilométrage du dernier entretien effectué")
    kilometrage_actuel = models.PositiveIntegerField(null=True, blank=True, help_text="Kilométrage actuel du véhicule (centralisé)")
    
    def __str__(self):
        label = f"{self.marque} {self.modele}".strip() or "À compléter"
        return f"{self.immatriculation} - {label}"

    def fiche_incomplete(self):
        """True si des infos importantes manquent (enregistrement partiel)."""
        missing = []
        if not (self.marque or '').strip():
            missing.append('marque')
        if not (self.modele or '').strip():
            missing.append('modele')
        if not self.numero_chassis:
            missing.append('chassis')
        if not (self.numero_moteur or '').strip():
            missing.append('moteur')
        if not (self.numero_carte_rose or '').strip():
            missing.append('carte_rose')
        if not self.date_expiration_assurance:
            missing.append('assurance')
        if not self.date_expiration_controle_technique:
            missing.append('controle')
        return missing

    def est_fiche_complete(self):
        return len(self.fiche_incomplete()) == 0

    def pneus_identifies(self):
        """Liste des pneus avec position et numéro (non vides)."""
        mapping = (
            ('Avant gauche', self.numero_pneu_avant_gauche),
            ('Avant droit', self.numero_pneu_avant_droit),
            ('Arrière gauche', self.numero_pneu_arriere_gauche),
            ('Arrière droit', self.numero_pneu_arriere_droit),
            ('Secours', self.numero_pneu_secours),
        )
        return [(pos, num) for pos, num in mapping if num]

    def pneus_resume(self):
        """Résumé une ligne pour exports listes."""
        parts = [f"{pos}: {num}" for pos, num in self.pneus_identifies()]
        return " | ".join(parts) if parts else ""
    
    def jours_avant_expiration_assurance(self):
        """Retourne le nombre de jours avant l'expiration de l'assurance"""
        if not self.date_expiration_assurance:
            return None
        return (self.date_expiration_assurance - timezone.now().date()).days
    
    def jours_avant_expiration_controle(self):
        """Retourne le nombre de jours avant l'expiration du contrôle technique"""
        if not self.date_expiration_controle_technique:
            return None
        return (self.date_expiration_controle_technique - timezone.now().date()).days
    
    def jours_avant_expiration_vignette(self):
        """Retourne le nombre de jours avant l'expiration de la vignette"""
        if not self.date_expiration_vignette:
            return None
        return (self.date_expiration_vignette - timezone.now().date()).days
    
    def entretien_necessaire(self, kilometrage_actuel):
        """Vérifie si un entretien est nécessaire (tous les 4500 km)"""
        dernier = self.kilometrage_dernier_entretien or 0
        actuel = kilometrage_actuel if kilometrage_actuel is not None else 0
        return actuel - dernier >= 4500
        
    def est_bloque_par_securite(self):
        """True si incident ouvert ou dernière checklist non conforme."""
        if self.incidents_securite.filter(statut='ouvert').exists():
            return True
        derniere = self.check_lists.order_by('-date_controle').first()
        return bool(derniere and derniere.statut == 'non_conforme')

    def est_disponible(self):
        """Véhicule libre, sans mission active et non bloqué par la sécurité."""
        if self.course_set.filter(statut__in=['validee', 'en_cours']).exists():
            return False
        return not self.est_bloque_par_securite()

    def date_prochain_entretien_estimee(self):
        """
        Estime la date du prochain entretien en fonction de la moyenne journalière
        de distance parcourue depuis le dernier entretien, ou affiche un message explicite.
        """
        from django.utils import timezone
        from suivi.models import SuiviVehicule
        # Récupérer la date du dernier entretien
        dernier_entretien_obj = self.entretiens.filter(statut='termine').order_by('-date_entretien').first()
        if not dernier_entretien_obj:
            return None, "Aucun entretien terminé enregistré pour ce véhicule."
        date_dernier_entretien = dernier_entretien_obj.date_entretien
        dernier_km = self.kilometrage_dernier_entretien
        # Récupérer tous les suivis depuis cette date
        suivis = SuiviVehicule.objects.filter(vehicule=self, date__gte=date_dernier_entretien).order_by('date')
        if not suivis.exists() or suivis.count() < 2:
            # Si on a au moins le kilométrage actuel, proposer une estimation simple
            if self.kilometrage_actuel is not None:
                km_restant = 4500 - (self.kilometrage_actuel - dernier_km)
                if km_restant > 0:
                    return None, f"Prochain entretien dans environ {km_restant} km (estimation basée sur le kilométrage actuel)."
                else:
                    return None, "Le véhicule a dépassé le seuil d'entretien recommandé (4500 km)."
            return None, "Pas assez de données de suivi pour estimer la date."
        # Calculer la distance totale parcourue et le nombre de jours
        distance_totale = sum(s.distance_parcourue for s in suivis)
        nb_jours = (suivis.last().date - suivis.first().date).days or 1
        moyenne_journaliere = distance_totale / nb_jours if nb_jours > 0 else 0
        if moyenne_journaliere == 0:
            return None, "Pas assez de données de suivi pour estimer la date."
        # Calculer le km restant avant prochain entretien
        dernier_suivi = suivis.last()
        km_actuel = dernier_suivi.distance_totale
        km_restant = 4500 - (km_actuel - dernier_km)
        if km_restant <= 0:
            return timezone.now().date(), "Le véhicule a dépassé le seuil d'entretien recommandé (4500 km)."
        jours_restant = int(km_restant / moyenne_journaliere)
        date_estimee = timezone.now().date() + timezone.timedelta(days=jours_restant)
        return date_estimee, None


class VehiculeAccessoire(models.Model):
    """Accessoire / équipement associé à un véhicule (liste dynamique)."""
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='accessoires')
    nom = models.CharField(max_length=120, verbose_name="Accessoire")
    quantite = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    remarque = models.CharField(max_length=255, blank=True, default='', verbose_name="Remarque")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'Accessoire véhicule'
        verbose_name_plural = 'Accessoires véhicule'

    def __str__(self):
        return f"{self.nom} (x{self.quantite}) — {self.vehicule.immatriculation}"


class Course(models.Model):
    """Modèle pour les courses/missions"""
    PRIORITE_CHOICES = [
        ('important', 'Important'),
        ('urgence', 'Urgence'),
        ('haute_urgence', 'Haute urgence'),
    ]
    etablissement = models.ForeignKey('Etablissement', on_delete=models.CASCADE, null=True, blank=True, related_name='courses')
    STATUS_CHOICES = (
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('refusee', 'Refusée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    )
    
    demandeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='courses_demandees')
    point_embarquement = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    # Coordonnées GPS planifiées (évaluation de course)
    embarquement_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    embarquement_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    destination_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    destination_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    rayon_arrivee_metres = models.PositiveIntegerField(
        default=150,
        help_text="Rayon de la zone d'arrivée autour de la destination (mètres)",
    )
    distance_prevue_km = models.FloatField(
        null=True,
        blank=True,
        help_text="Distance théorique embarquement → destination (vol d'oiseau)",
    )
    # Résultats d'évaluation GPS (mis à jour après analyse trajectoire)
    eval_arrivee_ok = models.BooleanField(null=True, blank=True)
    eval_heure_arrivee = models.DateTimeField(null=True, blank=True)
    eval_duree_arret_destination_s = models.PositiveIntegerField(null=True, blank=True)
    eval_ecart_trajet_km = models.FloatField(null=True, blank=True)
    eval_score = models.PositiveSmallIntegerField(null=True, blank=True)
    motif = models.TextField()
    nombre_passagers = models.PositiveIntegerField(default=1, verbose_name="Nombre de passagers")
    date_demande = models.DateTimeField(auto_now_add=True)
    date_souhaitee = models.DateTimeField(null=True, blank=True)
    
    # Champs remplis par le dispatcher
    chauffeur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_assignees')
    vehicule = models.ForeignKey(Vehicule, on_delete=models.SET_NULL, null=True, blank=True)
    dispatcher = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_dispatched')
    date_validation = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    
    # Champs remplis par le chauffeur
    kilometrage_depart = models.PositiveIntegerField(null=True, blank=True)
    kilometrage_fin = models.PositiveIntegerField(null=True, blank=True)
    date_depart = models.DateTimeField(null=True, blank=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    
    # Champ calculé
    distance_parcourue = models.PositiveIntegerField(null=True, blank=True)
    
    priorite = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='important',
        verbose_name='Priorité',
    )
    
    def __str__(self):
        return f"Course {self.id} - {self.demandeur.username} - {self.statut}"
    
    def save(self, *args, **kwargs):
        # Calcul de la distance parcourue (is not None pour ne pas ignorer 0)
        if self.kilometrage_fin is not None and self.kilometrage_depart is not None:
            self.distance_parcourue = self.kilometrage_fin - self.kilometrage_depart
        # Distance prévue embarquement → destination
        if (
            self.embarquement_latitude is not None and self.embarquement_longitude is not None
            and self.destination_latitude is not None and self.destination_longitude is not None
        ):
            try:
                from gps.services import haversine_km
                self.distance_prevue_km = round(haversine_km(
                    self.embarquement_latitude, self.embarquement_longitude,
                    self.destination_latitude, self.destination_longitude,
                ), 2)
            except Exception:
                pass
        # Mise à jour des dates
        if self.statut == 'validee' and not self.date_validation:
            self.date_validation = timezone.now()
        if self.statut == 'en_cours' and not self.date_depart:
            self.date_depart = timezone.now()
        if self.statut == 'terminee' and not self.date_fin:
            self.date_fin = timezone.now()
        # Historique kilométrage
        is_update = self.pk is not None
        if is_update:
            old = type(self).objects.get(pk=self.pk)
            km_fields = [('kilometrage_depart', old.kilometrage_depart, self.kilometrage_depart),
                         ('kilometrage_fin', old.kilometrage_fin, self.kilometrage_fin)]
            for champ, avant, apres in km_fields:
                if avant != apres and apres is not None:
                    from core.models import HistoriqueKilometrage
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.chauffeur,
                        module='course',
                        objet_id=self.pk,
                        valeur_avant=avant,
                        valeur_apres=apres,
                        commentaire=f"Modification du {champ} via Course #{self.pk}"
                    )
        super().save(*args, **kwargs)
        # Création (nouvelle course)
        if not is_update:
            for champ, apres in [('kilometrage_depart', self.kilometrage_depart), ('kilometrage_fin', self.kilometrage_fin)]:
                if apres is not None:
                    from core.models import HistoriqueKilometrage
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.chauffeur,
                        module='course',
                        objet_id=self.pk,
                        valeur_avant=None,
                        valeur_apres=apres,
                        commentaire=f"Création du {champ} via Course #{self.pk}"
                    )

    def clean(self):
        # Validation du kilométrage
        if self.kilometrage_depart is not None and self.kilometrage_fin is not None:
            if self.kilometrage_fin < self.kilometrage_depart:
                raise ValidationError("Le kilométrage d'arrivée ne peut pas être inférieur au kilométrage de départ.")
        # Vérification du dernier kilométrage connu (centralisé via vehicule.kilometrage_actuel)
        if self.vehicule_id:
            dernier_kilometrage = self.vehicule.kilometrage_actuel
            if dernier_kilometrage is not None:
                if self.kilometrage_depart is not None and self.kilometrage_depart < dernier_kilometrage:
                    raise ValidationError(
                        f"Le kilométrage de départ ({self.kilometrage_depart}) ne peut pas être inférieur "
                        f"au dernier kilométrage centralisé ({dernier_kilometrage})."
                    )
                if self.kilometrage_fin is not None and self.kilometrage_fin < dernier_kilometrage:
                    raise ValidationError(
                        f"Le kilométrage d'arrivée ({self.kilometrage_fin}) ne peut pas être inférieur "
                        f"au dernier kilométrage centralisé ({dernier_kilometrage})."
                    )

class ActionTraceur(models.Model):
    """Modèle pour tracer toutes les actions dans le système"""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.action} - {self.date_action}"

class HistoriqueKilometrage(models.Model):
    MODULE_CHOICES = (
        ('course', 'Course'),
        ('ravitaillement', 'Ravitaillement'),
        ('entretien', 'Entretien'),
    )
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='historiques_kilometrage')
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now_add=True)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    objet_id = models.PositiveIntegerField()
    valeur_avant = models.PositiveIntegerField(null=True, blank=True)
    valeur_apres = models.PositiveIntegerField(null=True, blank=True)
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.vehicule.immatriculation} - {self.module} - {self.valeur_avant} → {self.valeur_apres} ({self.date_modification:%d/%m/%Y %H:%M})"

class HistoriqueCorrectionKilometrage(models.Model):
    """Historique des corrections de kilométrage pour traçabilité"""
    vehicule = models.ForeignKey('Vehicule', on_delete=models.CASCADE, related_name='corrections_kilometrage')
    chauffeur = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='corrections_kilometrage')
    date_correction = models.DateTimeField(auto_now_add=True)
    valeur_avant = models.PositiveIntegerField()
    valeur_apres = models.PositiveIntegerField()
    motif = models.TextField(blank=True, null=True)
    auteur = models.ForeignKey('Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='corrections_kilometrage_auteur')

    def __str__(self):
        return f"Correction {self.vehicule.immatriculation} le {self.date_correction:%d/%m/%Y}"

    @classmethod
    def nombre_corrections(cls, vehicule, chauffeur=None):
        qs = cls.objects.filter(vehicule=vehicule)
        if chauffeur:
            qs = qs.filter(chauffeur=chauffeur)
        return qs.count()

class ApplicationControl(models.Model):
    is_open = models.BooleanField(default=True, verbose_name="Application ouverte")
    start_datetime = models.DateTimeField(default=timezone.now, verbose_name="Début d'utilisation autorisée")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="Fin d'utilisation autorisée")
    message = models.TextField(default="L'application est actuellement bloquée. Veuillez contacter l'administrateur.", blank=True)

    def __str__(self):
        return f"Ouvert: {self.is_open} | {self.start_datetime} - {self.end_datetime}"

class Message(models.Model):
    sender = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='messages_envoyes', null=True, blank=True)
    recipient = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='messages_recus')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_system_message = models.BooleanField(default=False, help_text="Indique si le message est un message système (non lié à un utilisateur spécifique)")

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"De {self.sender} à {self.recipient} le {timezone.localtime(self.timestamp).strftime('%Y-%m-%d %H:%M')}"
