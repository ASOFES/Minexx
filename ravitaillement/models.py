from django.db import models
from core.models import Utilisateur, Vehicule, ActionTraceur, Etablissement
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Station(models.Model):
    """Modèle pour les stations de ravitaillement"""
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='stations')
    nom = models.CharField(max_length=100, verbose_name="Nom de la station")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    ville = models.CharField(max_length=100, blank=True, null=True)
    code_postal = models.CharField(max_length=20, blank=True, null=True, verbose_name="Code postal")
    pays = models.CharField(max_length=100, default="République Démocratique du Congo")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True)
    est_active = models.BooleanField(default=True, verbose_name="Active")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "Station de ravitaillement"
        verbose_name_plural = "Stations de ravitaillement"
        ordering = ['nom']
        unique_together = ['etablissement', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.ville or 'Ville non spécifiée'})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.nom} {self.ville or ''}")
            self.slug = base_slug
            counter = 1
            while Station.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def adresse_complete(self):
        """Retourne l'adresse complète formatée"""
        parts = []
        if self.adresse:
            parts.append(self.adresse)
        if self.code_postal and self.ville:
            parts.append(f"{self.code_postal} {self.ville}")
        elif self.ville:
            parts.append(self.ville)
        if self.pays:
            parts.append(self.pays)
        return ", ".join(parts)

class Ravitaillement(models.Model):
    """Modèle pour les ravitaillements de véhicules"""
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='ravitaillements')
    date_ravitaillement = models.DateTimeField(auto_now_add=True)  # On garde auto_now_add pour simplifier
    station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True, related_name='ravitaillements', verbose_name="Station de ravitaillement")
    nom_station = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom de la station (si non répertoriée)", 
                                 help_text="À utiliser uniquement si la station n'est pas dans la liste")
    kilometrage_avant = models.PositiveIntegerField(default=0)
    kilometrage_apres = models.PositiveIntegerField(default=0)
    litres = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    cout_unitaire = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    cout_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    createur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='ravitaillements_crees')
    chauffeur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='ravitaillements_chauffeur')
    commentaires = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='images_ravitaillements/', blank=True, null=True, verbose_name="Photo du reçu")
    
    def __str__(self):
        return f"Ravitaillement {self.vehicule.immatriculation} - {self.date_ravitaillement}"
    
    def save(self, *args, **kwargs):
        from core.models import HistoriqueKilometrage  # Import local pour éviter les problèmes de boucle d'importation
        
        # Calcul automatique du coût total
        self.cout_total = self.litres * self.cout_unitaire
        # Capturer création/modification AVANT super().save()
        is_new = self.pk is None
        is_update = not is_new
        if is_update:
            old = type(self).objects.get(pk=self.pk)
            km_fields = [('kilometrage_avant', old.kilometrage_avant, self.kilometrage_avant),
                         ('kilometrage_apres', old.kilometrage_apres, self.kilometrage_apres)]
            for champ, avant, apres in km_fields:
                if avant != apres and apres is not None:
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.chauffeur or self.createur,
                        module='ravitaillement',
                        objet_id=self.pk,
                        valeur_avant=avant,
                        valeur_apres=apres,
                        commentaire=f"Modification du {champ} via Ravitaillement #{self.pk}"
                    )
        
        # Sauvegarde de l'instance
        super().save(*args, **kwargs)
        
        # Synchronisation du kilométrage actuel (is not None pour ne pas ignorer 0)
        if self.kilometrage_apres is not None and self.vehicule:
            if self.vehicule.kilometrage_actuel is None or self.kilometrage_apres > self.vehicule.kilometrage_actuel:
                self.vehicule.kilometrage_actuel = self.kilometrage_apres
                self.vehicule.save(update_fields=["kilometrage_actuel"])
        
        # Création (nouveau ravitaillement)
        if is_new:
            for champ, apres in [('kilometrage_avant', self.kilometrage_avant), ('kilometrage_apres', self.kilometrage_apres)]:
                if apres is not None:
                    HistoriqueKilometrage.objects.create(
                        vehicule=self.vehicule,
                        utilisateur=self.chauffeur or self.createur,
                        module='ravitaillement',
                        objet_id=self.pk,
                        valeur_avant=None,
                        valeur_apres=apres,
                        commentaire=f"Création du {champ} via Ravitaillement #{self.pk}"
                    )
            ActionTraceur.objects.create(
                utilisateur=self.createur,
                action="Ravitaillement",
                details=f"Véhicule: {self.vehicule.immatriculation}, Station: {self.nom_station or 'Non spécifiée'}, Litres: {self.litres}, Coût: {self.cout_total}"
            )
    
    @property
    def distance_parcourue(self):
        """Calcule la distance parcourue entre deux ravitaillements"""
        return self.kilometrage_apres - self.kilometrage_avant
    
    @property
    def consommation_moyenne(self):
        """Calcule la consommation moyenne en litres/100km"""
        if self.distance_parcourue > 0:
            return (self.litres * 100) / self.distance_parcourue
        return 0
    
    @classmethod
    def cout_total_par_vehicule(cls, vehicule):
        """Retourne le coût total des ravitaillements pour un véhicule"""
        from django.db.models import Sum
        return cls.objects.filter(vehicule=vehicule).aggregate(Sum('cout_total'))['cout_total__sum'] or 0
    
    @classmethod
    def cout_total_par_periode(cls, date_debut, date_fin):
        """Retourne le coût total des ravitaillements pour une période donnée"""
        from django.db.models import Sum
        return cls.objects.filter(date_ravitaillement__range=[date_debut, date_fin]).aggregate(Sum('cout_total'))['cout_total__sum'] or 0

    def clean(self):
        from core.models import Course # Import local pour éviter les boucles d'importation
        from entretien.models import Entretien # Import local pour éviter les boucles d'importation

        # Validation des champs de station
        if not self.station and not self.nom_station:
            raise ValidationError({
                'station': 'Veuillez sélectionner une station ou saisir un nom de station.',
                'nom_station': 'Veuillez sélectionner une station ou saisir un nom de station.'
            })
            
        # Si une station est sélectionnée, on utilise son nom
        if self.station:
            self.nom_station = self.station.nom
            
        # Validation que le kilométrage après est supérieur au kilométrage avant
        if self.kilometrage_apres <= self.kilometrage_avant:
            raise ValidationError({
                'kilometrage_apres': 'Le kilométrage au ravitaillement doit être strictement supérieur au kilométrage de référence.'
            })

        if self.litres is not None and self.litres <= 0:
            raise ValidationError({'litres': 'Le volume doit être strictement supérieur à 0 litre.'})
        if self.cout_unitaire is None or self.cout_unitaire <= 0:
            raise ValidationError({'cout_unitaire': 'Le prix unitaire doit être strictement supérieur à 0.'})

        # Vérification du dernier kilométrage connu AVANT la date de ce ravitaillement
        # Cette logique est appliquée uniquement si l'objet a déjà une date de ravitaillement et un véhicule, 
        # ce qui est nécessaire pour les requêtes chronologiques.
        if self.vehicule_id and self.date_ravitaillement:
            # Kilométrage du ravitaillement précédent (chronologiquement)
            previous_ravitaillement = Ravitaillement.objects.filter(
                vehicule=self.vehicule,
                date_ravitaillement__lt=self.date_ravitaillement # Strictement avant
            ).exclude(pk=self.pk).order_by('-date_ravitaillement').first()

            dernier_kilometrage_ravitaillement = previous_ravitaillement.kilometrage_apres if previous_ravitaillement and previous_ravitaillement.kilometrage_apres is not None else 0

            # Kilométrage de la dernière course terminée avant ce ravitaillement
            derniere_course_avant = Course.objects.filter(
                vehicule=self.vehicule,
                statut='terminee',
                date_fin__lt=self.date_ravitaillement # Strictement avant
            ).order_by('-date_fin').first()

            dernier_kilometrage_course = derniere_course_avant.kilometrage_fin if derniere_course_avant and derniere_course_avant.kilometrage_fin is not None else 0

            # Kilométrage du dernier entretien avant ce ravitaillement
            dernier_entretien_avant = Entretien.objects.filter(
                vehicule=self.vehicule,
                kilometrage_apres__isnull=False,
                date_entretien__lt=self.date_ravitaillement # Strictement avant
            ).order_by('-date_entretien').first()

            dernier_kilometrage_entretien = dernier_entretien_avant.kilometrage_apres if dernier_entretien_avant and dernier_entretien_avant.kilometrage_apres is not None else 0

            # Prendre le maximum des kilométrages trouvés avant la date de ce ravitaillement
            dernier_kilometrage_valide = max(dernier_kilometrage_ravitaillement, dernier_kilometrage_course, dernier_kilometrage_entretien)

            if self.kilometrage_avant < dernier_kilometrage_valide:
                raise ValidationError({
                    'kilometrage_avant': f'Le kilométrage avant ({self.kilometrage_avant}) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage_valide}) AVANT la date de ce ravitaillement.'
                })
            
            # Le kilométrage après doit aussi être supérieur ou égal au dernier kilométrage valide
            if self.kilometrage_apres < dernier_kilometrage_valide:
                raise ValidationError({
                    'kilometrage_apres': f'Le kilométrage après ({self.kilometrage_apres}) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage_valide}) AVANT la date de ce ravitaillement.'
                })
        else:
            # Si vehicule_id ou date_ravitaillement sont None (cas de nouvelle instance), 
            # on ne peut pas faire de validation chronologique ici. La validation sera 
            # faite par le champ lui-même ou par la vue après sauvegarde partielle.
            pass
