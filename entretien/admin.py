from django.contrib import admin
from .models import Entretien, ReparationMecanique, PieceRemplacee, LigneDevisReparation


class PieceRemplaceeInline(admin.TabularInline):
    model = PieceRemplacee
    extra = 0


class LigneDevisInline(admin.TabularInline):
    model = LigneDevisReparation
    extra = 0


class EntretienAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'garage', 'date_entretien', 'statut', 'cout', 'createur')
    list_filter = ('statut', 'date_entretien', 'vehicule')
    search_fields = ('vehicule__immatriculation', 'garage', 'motif', 'createur__username')
    date_hierarchy = 'date_entretien'
    readonly_fields = ('date_creation', 'date_modification')
    inlines = [PieceRemplaceeInline]


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
    inlines = [LigneDevisInline]
    fields = (
        'vehicule', 'incident', 'numero_dossier', 'titre', 'description', 'garage',
        'statut', 'devis_provisoire', 'devis_confirme',
        'date_signalement', 'date_debut_reparation', 'date_reparation',
        'bon_garage', 'piece_justificative', 'commentaires',
        'createur', 'confirme_par', 'date_creation', 'date_modification',
    )


admin.site.register(Entretien, EntretienAdmin)
