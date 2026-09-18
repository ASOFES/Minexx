from django.contrib import admin
from .models import Rapport

class RapportAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_rapport', 'format_rapport', 'date_debut', 'date_fin', 'date_generation', 'generateur')
    list_filter = ('type_rapport', 'format_rapport', 'date_generation')
    search_fields = ('titre', 'generateur__username')
    date_hierarchy = 'date_generation'
    readonly_fields = ('date_generation',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'type_rapport', 'format_rapport', 'generateur')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Fichier', {
            'fields': ('fichier', 'parametres')
        }),
    )

admin.site.register(Rapport, RapportAdmin)
