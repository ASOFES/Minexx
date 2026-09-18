from django.db import models
from core.models import Utilisateur, ActionTraceur

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
    parametres = models.JSONField(blank=True, null=True)  # Pour stocker des paramètres spécifiques au rapport
    
    def __str__(self):
        return f"{self.titre} - {self.date_generation}"
    
    def save(self, *args, **kwargs):
        # Créer une entrée dans le traceur d'actions
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            ActionTraceur.objects.create(
                utilisateur=self.generateur,
                action="Génération de rapport",
                details=f"Type: {self.get_type_rapport_display()}, Période: {self.date_debut} - {self.date_fin}"
            )
