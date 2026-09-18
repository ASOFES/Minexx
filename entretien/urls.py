from django.urls import path
from . import views

app_name = 'entretien'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ajouter/', views.creer_entretien, name='creer_entretien'),
    path('liste/', views.liste_entretiens, name='liste_entretiens'),
    path('get-vehicule-kilometrage/', views.get_vehicule_kilometrage, name='get_vehicule_kilometrage'),
    path('exporter-entretiens-pdf/', views.exporter_entretiens_pdf, name='exporter_entretiens_pdf'),
    path('exporter-entretiens-excel/', views.exporter_entretiens_excel, name='exporter_entretiens_excel'),
    path('detail/<int:entretien_id>/', views.detail_entretien, name='detail_entretien'),
    path('modifier/<int:entretien_id>/', views.modifier_entretien, name='modifier_entretien'),
    path('supprimer/<int:entretien_id>/', views.supprimer_entretien, name='supprimer_entretien'),
    path('exporter-entretien-pdf/<int:entretien_id>/', views.exporter_entretien_pdf, name='exporter_entretien_pdf'),
    path('exporter-entretien-excel/<int:entretien_id>/', views.exporter_entretien_excel, name='exporter_entretien_excel'),
    # Exemple : path('', views.ma_vue, name='nom_url'),
]
