from django.conf import settings
from django.db import models
from django.utils import timezone


class GPSPosition(models.Model):
    """Point GPS enregistré uniquement pendant une mission active (ou synchronisé après coup)."""

    EVENT_CHOICES = (
        ('ping', 'Position'),
        ('depart', 'Départ'),
        ('arrivee', 'Arrivée destination'),
        ('retour', 'Retour'),
        ('fin', 'Fin de mission'),
    )

    course = models.ForeignKey(
        'core.Course',
        on_delete=models.CASCADE,
        related_name='positions_gps',
    )
    chauffeur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions_gps',
    )
    vehicule = models.ForeignKey(
        'core.Vehicule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions_gps',
    )
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    timestamp = models.DateTimeField(db_index=True)
    vitesse = models.FloatField(null=True, blank=True, help_text='km/h')
    heading = models.FloatField(null=True, blank=True, help_text='Direction en degrés 0-360')
    accuracy = models.FloatField(null=True, blank=True, help_text='Précision GPS en mètres')
    kilometrage = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Kilométrage GPS / odomètre au moment du point',
    )
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, default='ping')
    battery_level = models.PositiveSmallIntegerField(null=True, blank=True)
    synced_at = models.DateTimeField(auto_now_add=True)
    client_id = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text='ID client pour déduplication offline',
        db_index=True,
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['course', 'timestamp']),
            models.Index(fields=['vehicule', 'timestamp']),
            models.Index(fields=['chauffeur', 'timestamp']),
        ]
        verbose_name = 'Position GPS'
        verbose_name_plural = 'Positions GPS'

    def __str__(self):
        return f"GPS #{self.pk} mission {self.course_id} @ {self.timestamp}"


class GPSAccessLog(models.Model):
    """Journal d'accès à l'historique GPS (confidentialité)."""

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gps_access_logs',
    )
    course = models.ForeignKey(
        'core.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='gps_access_logs',
    )
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, default='')
    date_acces = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_acces']
        verbose_name = 'Accès historique GPS'
        verbose_name_plural = 'Accès historiques GPS'

    def __str__(self):
        return f"{self.utilisateur} — {self.action} — {self.date_acces}"


class GPSSettings(models.Model):
    """Paramètres organisationnels (singleton logique par établissement)."""

    etablissement = models.OneToOneField(
        'core.Etablissement',
        on_delete=models.CASCADE,
        related_name='gps_settings',
        null=True,
        blank=True,
    )
    retention_jours = models.PositiveIntegerField(
        default=365,
        help_text='Durée de conservation des positions GPS (jours)',
    )
    intervalle_secondes = models.PositiveIntegerField(
        default=10,
        help_text='Intervalle recommandé d’envoi (5–15 s)',
    )
    suivi_uniquement_mission_active = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paramètres GPS'
        verbose_name_plural = 'Paramètres GPS'

    def __str__(self):
        nom = self.etablissement.nom if self.etablissement_id else 'Global'
        return f"GPS settings — {nom}"

    @classmethod
    def get_for_etablissement(cls, etablissement):
        if etablissement is None:
            obj, _ = cls.objects.get_or_create(etablissement=None)
            return obj
        obj, _ = cls.objects.get_or_create(etablissement=etablissement)
        return obj
