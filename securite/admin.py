from django.contrib import admin
from .models import CheckListSecurite

class CheckListSecuriteAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'controleur', 'lieu_controle', 'date_controle', 'kilometrage')
    list_filter = ('date_controle', 'vehicule', 'controleur')
    search_fields = ('vehicule__immatriculation', 'controleur__username', 'commentaires', 'lieu_controle')
    date_hierarchy = 'date_controle'
    readonly_fields = ('date_controle',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('vehicule', 'controleur', 'lieu_controle', 'kilometrage')
        }),
        ('Check-list', {
            'fields': ('parebrise_avant', 'parebrise_arriere', 'retroviseur_gauche', 'retroviseur_droit',
                      'clignotant', 'feu_arriere_gauche', 'feu_arriere_droit', 'feu_position_gauche', 'feu_position_droit')
        }),
        ('Commentaires', {
            'fields': ('commentaires',)
        }),
    )

admin.site.register(CheckListSecurite, CheckListSecuriteAdmin)
