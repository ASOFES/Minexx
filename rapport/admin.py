from django.contrib import admin
from .models import Rapport, BudgetFlotte, AchatDocumentBord


class RapportAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_rapport', 'format_rapport', 'date_debut', 'date_fin', 'date_generation', 'generateur')
    list_filter = ('type_rapport', 'format_rapport', 'date_generation')
    search_fields = ('titre', 'generateur__username')
    date_hierarchy = 'date_generation'
    readonly_fields = ('date_generation',)


@admin.register(BudgetFlotte)
class BudgetFlotteAdmin(admin.ModelAdmin):
    list_display = (
        'periode_type', 'annee', 'mois', 'etablissement',
        'budget_carburant', 'budget_entretien', 'budget_reparations',
        'budget_documents_bord', 'budget_divers',
    )
    list_filter = ('periode_type', 'annee', 'etablissement')
    search_fields = ('notes',)


@admin.register(AchatDocumentBord)
class AchatDocumentBordAdmin(admin.ModelAdmin):
    list_display = ('date_achat', 'vehicule', 'type_document', 'montant', 'date_expiration')
    list_filter = ('type_document', 'date_achat')
    search_fields = ('vehicule__immatriculation', 'libelle', 'notes')


admin.site.register(Rapport, RapportAdmin)
