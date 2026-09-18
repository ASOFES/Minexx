from django.contrib import admin
from .models import SuiviVehicule

class SuiviVehiculeAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'date', 'distance_parcourue', 'nombre_courses')
    list_filter = ('date', 'vehicule')
    search_fields = ('vehicule__immatriculation',)
    date_hierarchy = 'date'
    readonly_fields = ('vehicule', 'date', 'distance_parcourue', 'nombre_courses')

admin.site.register(SuiviVehicule, SuiviVehiculeAdmin)
