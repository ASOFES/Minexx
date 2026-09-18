from django.db import models
from core.models import Utilisateur, Course, Vehicule, ActionTraceur

class HistoriqueDispatch(models.Model):
    """Modèle pour suivre l'historique des actions du dispatcher"""
    dispatcher = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='historique_dispatch')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='historique_dispatch')
    date_action = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # 'assignation', 'validation', 'refus', 'mise_en_attente'
    chauffeur_assigne = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='historique_assignations')
    vehicule_assigne = models.ForeignKey(Vehicule, on_delete=models.SET_NULL, null=True, blank=True, related_name='historique_assignations')
    commentaire = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.action} par {self.dispatcher.username} - Course {self.course.id}"
    
    def save(self, *args, **kwargs):
        # Créer une entrée dans le traceur d'actions
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            details = f"Course {self.course.id}"
            if self.chauffeur_assigne:
                details += f", Chauffeur: {self.chauffeur_assigne.username}"
            if self.vehicule_assigne:
                details += f", Véhicule: {self.vehicule_assigne.immatriculation}"
            
            ActionTraceur.objects.create(
                utilisateur=self.dispatcher,
                action=f"Dispatch: {self.action}",
                details=details
            )
