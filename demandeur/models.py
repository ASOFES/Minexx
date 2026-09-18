from django.db import models
from core.models import Utilisateur, Course

class HistoriqueDemande(models.Model):
    """Modèle pour suivre l'historique des demandes de mission"""
    demandeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='historique_demandes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='historique')
    date_demande = models.DateTimeField(auto_now_add=True)
    statut_initial = models.CharField(max_length=20, choices=Course.STATUS_CHOICES)
    
    def __str__(self):
        return f"Demande de {self.demandeur.username} - {self.date_demande}"
