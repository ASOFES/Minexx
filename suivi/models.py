from django.db import models
from core.models import Vehicule
from django.db.models import Sum
from entretien.models import Entretien
from ravitaillement.models import Ravitaillement

class SuiviVehicule(models.Model):
    """Modèle pour le suivi des véhicules"""
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='suivis')
    date = models.DateField()
    date_immatriculation = models.DateField(null=True, blank=True)
    distance_parcourue = models.PositiveIntegerField(default=0)
    distance_totale = models.PositiveIntegerField(default=0)
    nombre_courses = models.PositiveIntegerField(default=0)
    nombre_entretiens = models.PositiveIntegerField(default=0)
    volume_carburant_consomme = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    class Meta:
        unique_together = ('vehicule', 'date')
    
    def __str__(self):
        return f"Suivi {self.vehicule.immatriculation} - {self.date} - {self.distance_parcourue} km"
    
    @classmethod
    def mettre_a_jour_suivi(cls, vehicule, date, distance):
        """Met à jour le suivi journalier pour un véhicule"""
        obj, created = cls.objects.get_or_create(
            vehicule=vehicule,
            date=date,
            defaults={
                'distance_parcourue': distance, 
                'nombre_courses': 1,
                'date_immatriculation': vehicule.date_immatriculation if hasattr(vehicule, 'date_immatriculation') else None
            }
        )
        
        if not created:
            obj.distance_parcourue += distance
            obj.nombre_courses += 1
            obj.save()
        
        # Mettre à jour la distance totale
        obj.distance_totale = cls.distance_totale_par_vehicule(vehicule)
        
        # Mettre à jour le nombre d'entretiens
        obj.nombre_entretiens = Entretien.objects.filter(vehicule=vehicule).count()
        
        # Mettre à jour le volume de carburant consommé
        obj.volume_carburant_consomme = Ravitaillement.objects.filter(
            vehicule=vehicule
        ).aggregate(Sum('litres'))['litres__sum'] or 0
        
        obj.save()
        
        return obj
    
    @classmethod
    def distance_totale_par_vehicule(cls, vehicule):
        """Retourne la distance totale parcourue par un véhicule"""
        return cls.objects.filter(vehicule=vehicule).aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
    
    @classmethod
    def distance_par_periode(cls, vehicule, date_debut, date_fin):
        """Retourne la distance parcourue par un véhicule sur une période donnée"""
        return cls.objects.filter(
            vehicule=vehicule, 
            date__range=[date_debut, date_fin]
        ).aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
