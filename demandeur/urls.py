from django.urls import path
from . import views

app_name = 'demandeur'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('nouvelle-demande/', views.nouvelle_demande, name='nouvelle_demande'),
    path('demande/<int:demande_id>/', views.detail_demande, name='detail_demande'),
    path('demande/<int:demande_id>/modifier/', views.modifier_demande, name='modifier_demande'),
    path('demande/<int:demande_id>/annuler/', views.annuler_demande, name='annuler_demande'),
    path('demande/<int:demande_id>/pdf/', views.demande_pdf, name='demande_pdf'),
    path('demande/<int:demande_id>/excel/', views.demande_excel, name='demande_excel'),
    path('demandes/pdf/', views.demandes_pdf, name='demandes_pdf'),
    path('demandes/excel/', views.demandes_excel, name='demandes_excel'),

    path('export-courses-jour-pdf/', views.export_courses_jour_pdf, name='export_courses_jour_pdf'),
    path('export-courses-jour-excel/', views.export_courses_jour_excel, name='export_courses_jour_excel'),
    path('notifier-chauffeurs/', views.notifier_chauffeurs, name='notifier_chauffeurs'),
]
