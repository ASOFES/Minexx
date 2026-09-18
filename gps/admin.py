from django.contrib import admin
from .models import GPSPosition, GPSAccessLog, GPSSettings


@admin.register(GPSPosition)
class GPSPositionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'course', 'chauffeur', 'vehicule',
        'latitude', 'longitude', 'vitesse', 'event_type', 'timestamp',
    )
    list_filter = ('event_type', 'timestamp')
    search_fields = ('course__id', 'chauffeur__username', 'vehicule__immatriculation', 'client_id')
    raw_id_fields = ('course', 'chauffeur', 'vehicule')
    date_hierarchy = 'timestamp'


@admin.register(GPSAccessLog)
class GPSAccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'course', 'action', 'date_acces')
    list_filter = ('action', 'date_acces')
    search_fields = ('utilisateur__username', 'details')
    raw_id_fields = ('utilisateur', 'course')


@admin.register(GPSSettings)
class GPSSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'etablissement', 'actif', 'retention_jours',
        'intervalle_secondes', 'suivi_uniquement_mission_active',
    )
