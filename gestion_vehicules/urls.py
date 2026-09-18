"""
URL configuration for gestion_vehicules project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('demandeur/', include('demandeur.urls')),
    path('dispatch/', include('dispatch.urls')),
    path('chauffeur/', include('chauffeur.urls')),
    path('securite/', include('securite.urls')),
    path('entretien/', include('entretien.urls')),
    path('ravitaillement/', include('ravitaillement.urls')),
    path('suivi/', include('suivi.urls')),
    path('gps/', include('gps.urls')),
    path('rapport/', include('rapport.urls')),
    path('notifications/', include('notifications.urls')),
    # path('chat/', include('chat.urls')),  # Module chat désactivé car non présent
]

# Fichiers uploadés (photos véhicules, etc.)
# django.conf.urls.static.static() ne sert RIEN si DEBUG=False — d'où images cassées sur Railway.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            media_serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': False},
        ),
    ]
