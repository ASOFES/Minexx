from django.contrib import admin
from .models import Entretien, ReparationMecanique


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


@admin.register(ReparationMecanique)
class ReparationMecaniqueAdmin(admin.ModelAdmin):
    list_display = (
        'vehicule', 'titre', 'statut', 'devis_provisoire', 'devis_confirme',
        'date_signalement', 'date_reparation',
    )
    list_filter = ('statut', 'date_signalement')
    search_fields = ('vehicule__immatriculation', 'titre', 'description', 'garage')
    date_hierarchy = 'date_signalement'
    readonly_fields = ('date_creation', 'date_modification', 'confirme_par')


admin.site.register(Entretien, EntretienAdmin)
