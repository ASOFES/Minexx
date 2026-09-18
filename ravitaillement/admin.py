from django.contrib import admin
from .models import Ravitaillement, Station

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'pays', 'est_active', 'date_creation')
    list_filter = ('est_active', 'ville', 'pays')
    search_fields = ('nom', 'adresse', 'ville', 'code_postal', 'pays')
    list_editable = ('est_active',)
    readonly_fields = ('date_creation', 'date_maj', 'slug')
    fieldsets = (
        ('Informations de base', {
            'fields': ('etablissement', 'nom', 'est_active')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'code_postal', 'ville', 'pays')
        }),
        ('Contact', {
            'fields': ('telephone', 'email')
        }),
        ('Métadonnées', {
            'fields': ('slug', 'date_creation', 'date_maj'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(etablissement=request.user.etablissement)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.etablissement = request.user.etablissement
        super().save_model(request, obj, form, change)


@admin.register(Ravitaillement)
class RavitaillementAdmin(admin.ModelAdmin):
    list_display = ('vehicule', 'date_ravitaillement', 'get_station', 'litres', 'cout_unitaire', 'cout_total')
    list_filter = ('vehicule', 'date_ravitaillement', 'station')
    search_fields = ('vehicule__immatriculation', 'nom_station', 'station__nom', 'commentaires')
    date_hierarchy = 'date_ravitaillement'
    readonly_fields = ('cout_total', 'date_ravitaillement')  # Suppression des champs qui n'existent pas dans le modèle
    
    def get_station(self, obj):
        if obj.station:
            return obj.station.nom
        return obj.nom_station or "-"
    get_station.short_description = "Station"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(etablissement=request.user.etablissement)
    
    def save_model(self, request, obj, form, change):
        if not change and not hasattr(obj, 'etablissement'):
            obj.etablissement = request.user.etablissement
        super().save_model(request, obj, form, change)
    fieldsets = (
        ('Informations générales', {
            'fields': ('vehicule', 'createur')
        }),
        ('Kilométrage', {
            'fields': ('kilometrage_avant', 'kilometrage_apres')
        }),
        ('Carburant', {
            'fields': ('litres', 'cout_unitaire', 'cout_total')
        }),
        ('Commentaires', {
            'fields': ('commentaires',)
        }),
    )

# Le modèle Ravitaillement est déjà enregistré avec le décorateur @admin.register
