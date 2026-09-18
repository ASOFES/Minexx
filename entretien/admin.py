from django.contrib import admin
from .models import Entretien

class EntretienAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'garage', 'date_entretien', 'statut', 'cout', 'createur')
    list_filter = ('statut', 'date_entretien', 'vehicule')
    search_fields = ('vehicule__immatriculation', 'garage', 'motif', 'createur__username')
    date_hierarchy = 'date_entretien'
    readonly_fields = ('date_creation', 'date_modification')
    fieldsets = (
        ('Informations générales', {
            'fields': ('vehicule', 'garage', 'date_entretien', 'statut', 'createur')
        }),
        ('Détails', {
            'fields': ('motif', 'cout', 'commentaires')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(Entretien, EntretienAdmin)
