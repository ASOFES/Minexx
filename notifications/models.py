from django.db import models
from django.utils import timezone
from core.models import Vehicule
from django.conf import settings

class DocumentNotification(models.Model):
    """Modèle pour suivre les notifications de documents de bord"""
    DOCUMENT_TYPES = (
        ('carte_grise', 'Carte Grise'),
        ('assurance', 'Assurance'),
        ('controle_technique', 'Contrôle Technique'),
        ('vignette', 'Vignette'),
        ('stationnement', 'Stationnement'),
    ) 
    
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='document_notifications')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    date_expiration = models.DateField()
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification de document"
        verbose_name_plural = "Notifications de documents"
        ordering = ['date_expiration']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.vehicule.immatriculation} - {self.date_expiration}"
    
    @property
    def jours_restants(self):
        return (self.date_expiration - timezone.now().date()).days
    
    @property
    def est_expire(self):
        return self.jours_restants < 0
    
    @property
    def statut(self):
        if self.est_expire:
            return 'expiré'
        elif self.jours_restants <= 7:
            return 'alerte'
        return 'ok'

class EntretienNotification(models.Model):
    """Modèle pour suivre les notifications d'entretien"""
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE, related_name='entretien_notifications')
    kilometrage_actuel = models.PositiveIntegerField()
    kilometrage_prochain = models.PositiveIntegerField(help_text="Kilométrage auquel le prochain entretien est nécessaire")
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification d'entretien"
        verbose_name_plural = "Notifications d'entretien"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Entretien - {self.vehicule.immatriculation} - {self.kilometrage_actuel}km"
    
    @property
    def kilometres_restants(self):
        return self.kilometrage_prochain - self.kilometrage_actuel
    
    @property
    def statut(self):
        if self.kilometres_restants <= 0:
            return 'en_retard'
        elif self.kilometres_restants <= 500:
            return 'alerte'
        return 'ok'


class PermisNotification(models.Model):
    """Suivi des notifications d'expiration de permis chauffeur."""
    chauffeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='permis_notifications',
    )
    date_expiration = models.DateField()
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notification de permis"
        verbose_name_plural = "Notifications de permis"
        ordering = ['date_expiration']

    def __str__(self):
        return f"Permis - {self.chauffeur} - {self.date_expiration}"

    @property
    def jours_restants(self):
        return (self.date_expiration - timezone.now().date()).days

    @property
    def est_expire(self):
        return self.jours_restants < 0

    @property
    def statut(self):
        if self.est_expire:
            return 'expiré'
        elif self.jours_restants <= 30:
            return 'alerte'
        return 'ok'


class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    endpoint = models.TextField(default='')
    auth = models.CharField(max_length=255, default='')
    p256dh = models.CharField(max_length=255, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSubscription({self.user})"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.message[:20]}"
