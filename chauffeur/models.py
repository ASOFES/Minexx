from django.db import models
from core.models import Utilisateur, Course, Vehicule, ActionTraceur

class HistoriqueChauffeur(models.Model):
    """Modèle pour suivre l'historique des actions du chauffeur"""
    chauffeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='historique_chauffeur')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='historique_chauffeur')
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='historique_chauffeur')
    date_action = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # 'depart', 'arrivee'
    kilometrage = models.PositiveIntegerField()
    commentaire = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.action} par {self.chauffeur.username} - Course {self.course.id}"
    
    def save(self, *args, **kwargs):
        # Créer une entrée dans le traceur d'actions
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            ActionTraceur.objects.create(
                utilisateur=self.chauffeur,
                action=f"Chauffeur: {self.action}",
                details=f"Course {self.course.id}, Véhicule: {self.vehicule.immatriculation}, Kilométrage: {self.kilometrage}"
            )

class DistanceJournaliere(models.Model):
    """Modèle pour suivre la distance journalière par chauffeur"""
    chauffeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='distances_journalieres')
    date = models.DateField()
    distance_totale = models.PositiveIntegerField(default=0)
    nombre_courses = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['chauffeur', 'date']
        verbose_name = "Distance journalière"
        verbose_name_plural = "Distances journalières"
    
    def __str__(self):
        return f"{self.chauffeur.username} - {self.date} - {self.distance_totale} km"

class CommentaireRapportChauffeur(models.Model):
    """Commentaires ou appréciations sur un rapport chauffeur pour une période donnée"""
    chauffeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commentaires_rapport')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='commentaires_ecrits')
    date_debut = models.DateField()
    date_fin = models.DateField()
    texte = models.TextField()
    date_commentaire = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire {self.chauffeur.username} du {self.date_commentaire:%d/%m/%Y}"

class CommentaireRapportDemandeur(models.Model):
    """Commentaires ou appréciations sur un rapport demandeur pour une période donnée"""
    demandeur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='commentaires_rapport_demandeur')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name='commentaires_ecrits_demandeur')
    date_debut = models.DateField()
    date_fin = models.DateField()
    texte = models.TextField()
    date_commentaire = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire demandeur {self.demandeur.username} du {self.date_commentaire:%d/%m/%Y}"
