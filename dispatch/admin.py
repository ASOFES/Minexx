from django.contrib import admin
from .models import HistoriqueDispatch

class HistoriqueDispatchAdmin(admin.ModelAdmin):
    list_display = ('dispatcher', 'course', 'action', 'date_action', 'chauffeur_assigne', 'vehicule_assigne')
    list_filter = ('action', 'date_action')
    search_fields = ('dispatcher__username', 'course__id', 'chauffeur_assigne__username', 'vehicule_assigne__immatriculation')
    date_hierarchy = 'date_action'
    readonly_fields = ('dispatcher', 'course', 'date_action', 'action', 'chauffeur_assigne', 'vehicule_assigne', 'commentaire')

admin.site.register(HistoriqueDispatch, HistoriqueDispatchAdmin)
