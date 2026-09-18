from core.models import Course
from django.db.models import Count
from django.db import connection

# Afficher la distribution des statuts
stats = Course.objects.values('statut').annotate(count=Count('id')).order_by('statut')
print("\nDistribution des statuts des missions :")
print("-" * 40)
for stat in stats:
    print(f"{stat['statut']}: {stat['count']} missions")

# Vérifier les requêtes SQL générées
print("\nRequête SQL utilisée :")
print("-" * 40)
print(str(Course.objects.filter(statut='en_cours').query)) 