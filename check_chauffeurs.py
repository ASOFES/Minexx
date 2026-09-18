from core.models import Course, Utilisateur
from django.db.models import Count, Sum
from django.db import connection

# Vérifier les chauffeurs
chauffeurs = Utilisateur.objects.filter(role='chauffeur')
print("\nNombre total de chauffeurs:", chauffeurs.count())
print("\nChauffeurs par établissement:")
for etab in chauffeurs.values('etablissement__nom').annotate(count=Count('id')):
    print(f"- {etab['etablissement__nom']}: {etab['count']} chauffeurs")

# Vérifier les missions des chauffeurs
print("\nMissions par statut pour les chauffeurs:")
stats = Course.objects.filter(chauffeur__isnull=False).values('statut').annotate(
    count=Count('id'),
    chauffeurs=Count('chauffeur', distinct=True)
).order_by('statut')
for stat in stats:
    print(f"- {stat['statut']}: {stat['count']} missions ({stat['chauffeurs']} chauffeurs)")

# Vérifier les missions terminées par chauffeur
print("\nMissions terminées par chauffeur:")
chauffeurs_stats = Course.objects.filter(statut='terminee').values(
    'chauffeur__username',
    'chauffeur__first_name',
    'chauffeur__last_name',
    'chauffeur__etablissement__nom'
).annotate(
    nb_missions=Count('id'),
    distance_totale=Sum('distance_parcourue')
).order_by('-nb_missions')
for stat in chauffeurs_stats:
    print(f"- {stat['chauffeur__first_name']} {stat['chauffeur__last_name']} ({stat['chauffeur__etablissement__nom']}):")
    print(f"  * {stat['nb_missions']} missions")
    print(f"  * {stat['distance_totale'] or 0} km au total")

# Vérifier la requête SQL
print("\nRequête SQL pour le rapport des chauffeurs:")
queryset = Course.objects.filter(statut='terminee')
print(str(queryset.query)) 