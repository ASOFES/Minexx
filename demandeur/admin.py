from django.contrib import admin
from .models import HistoriqueDemande

class HistoriqueDemandeAdmin(admin.ModelAdmin):
    list_display = ('demandeur', 'course', 'date_demande', 'statut_initial')
    list_filter = ('statut_initial', 'date_demande')
    search_fields = ('demandeur__username', 'course__id')
    date_hierarchy = 'date_demande'
    readonly_fields = ('demandeur', 'course', 'date_demande', 'statut_initial')

admin.site.register(HistoriqueDemande, HistoriqueDemandeAdmin)
