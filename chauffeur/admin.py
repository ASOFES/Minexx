from django.contrib import admin
from .models import HistoriqueChauffeur, DistanceJournaliere

class HistoriqueChauffeurAdmin(admin.ModelAdmin):
    list_display = ('chauffeur', 'course', 'vehicule', 'action', 'kilometrage', 'date_action')
    list_filter = ('action', 'date_action')
    search_fields = ('chauffeur__username', 'course__id', 'vehicule__immatriculation')
    date_hierarchy = 'date_action'
    readonly_fields = ('chauffeur', 'course', 'vehicule', 'date_action', 'action', 'kilometrage')

class DistanceJournaliereAdmin(admin.ModelAdmin):
    list_display = ('chauffeur', 'date', 'distance_totale', 'nombre_courses')
    list_filter = ('date',)
    search_fields = ('chauffeur__username',)
    date_hierarchy = 'date'
    readonly_fields = ('chauffeur', 'date', 'distance_totale', 'nombre_courses')

admin.site.register(HistoriqueChauffeur, HistoriqueChauffeurAdmin)
admin.site.register(DistanceJournaliere, DistanceJournaliereAdmin)
