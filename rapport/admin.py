from django.contrib import admin
from .models import Rapport, BudgetFlotte


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
        'budget_carburant', 'budget_entretien', 'budget_reparations', 'budget_divers',
    )
    list_filter = ('periode_type', 'annee', 'etablissement')
    search_fields = ('notes',)


admin.site.register(Rapport, RapportAdmin)
