from django.urls import path
from django.views.generic import TemplateView
from .views import (
    dashboard, liste_ravitaillements, creer_ravitaillement, detail_ravitaillement,
    modifier_ravitaillement, supprimer_ravitaillement, exporter_ravitaillements_pdf,
    exporter_ravitaillements_excel, exporter_ravitaillement_pdf, exporter_ravitaillement_excel,
    get_vehicule_kilometrage, StationListView, StationCreateView, StationUpdateView,
    toggle_station_status, supprimer_station
)

app_name = 'ravitaillement'

urlpatterns = [
    # URLs pour les ravitaillements
    path('', dashboard, name='dashboard'),
    path('liste/', liste_ravitaillements, name='liste_ravitaillements'),
    path('ajouter/', creer_ravitaillement, name='ajouter_ravitaillement'),
    path('detail/<int:ravitaillement_id>/', detail_ravitaillement, name='detail_ravitaillement'),
    path('modifier/<int:ravitaillement_id>/', modifier_ravitaillement, name='modifier_ravitaillement'),
    path('supprimer/<int:ravitaillement_id>/', supprimer_ravitaillement, name='supprimer_ravitaillement'),
    
    # URLs pour les stations
    path('stations/', StationListView.as_view(), name='liste_stations'),
    path('stations/ajouter/', StationCreateView.as_view(), name='ajouter_station'),
    path('stations/modifier/<int:pk>/', StationUpdateView.as_view(), name='modifier_station'),
    path('stations/toggle-status/<int:pk>/', toggle_station_status, name='toggle_station_status'),
    path('stations/supprimer/<int:pk>/', supprimer_station, name='supprimer_station'),
    
    # Export routes
    path('export/pdf/', exporter_ravitaillements_pdf, name='exporter_ravitaillements_pdf'),
    path('export/excel/', exporter_ravitaillements_excel, name='exporter_ravitaillements_excel'),
    path('export/<int:ravitaillement_id>/pdf/', exporter_ravitaillement_pdf, name='exporter_ravitaillement_pdf'),
    path('export/<int:ravitaillement_id>/excel/', exporter_ravitaillement_excel, name='exporter_ravitaillement_excel'),
    
    # API routes
    path('api/vehicule/kilometrage/', get_vehicule_kilometrage, name='get_vehicule_kilometrage'),
    
    # Autres URLs
    path('help/', TemplateView.as_view(template_name='ravitaillement/help.html'), name='help'),
]
