from django.urls import path
from . import views

app_name = 'dispatch'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('demande/<int:demande_id>/', views.detail_demande, name='detail_demande'),
    path('demande/<int:demande_id>/traiter/', views.traiter_demande, name='traiter_demande'),
    
    # URL pour la liste des courses (nouvelle)
    path('courses/', views.dashboard, name='liste_courses'),
    
    # URLs pour le suivi kilométrique
    path('suivi-kilometrage/', views.suivi_kilometrage, name='suivi_kilometrage'),
    path('suivi-kilometrage/excel/', views.export_suivi_kilometrage_excel, name='suivi_kilometrage_excel'),
    
    # URLs pour l'exportation
    path('demande/<int:course_id>/pdf/', views.course_detail_pdf, name='course_detail_pdf'),
    path('demande/<int:course_id>/excel/', views.course_detail_excel, name='course_detail_excel'),
    path('courses/pdf/', views.courses_list_pdf, name='courses_list_pdf'),
    path('courses/excel/', views.courses_list_excel, name='courses_list_excel'),
]
