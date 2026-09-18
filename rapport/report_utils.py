"""
Helpers de cohérence pour les rapports flotte MINEXX.

Conventions :
- Missions / activité course : filtre principal sur date_depart (fin : date_fin si dispo).
- Demandes : date_demande.
- Carburant : date_ravitaillement ; L/100km = litres (avec Δkm>0) / somme(Δkm) * 100.
- Entretien : date_entretien.
- Coût/km = (carburant + entretien) / distance_missions — jamais un forfait fictif.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional

from django.db.models import Q, QuerySet, Sum
from django.db.models.functions import Coalesce

from core.models import Course, Vehicule
from entretien.models import Entretien
from ravitaillement.models import Ravitaillement


def is_rapport_user(user) -> bool:
    return bool(
        user.is_authenticated
        and (getattr(user, 'role', None) in ('admin', 'dispatch') or user.is_superuser)
    )


def scope_etablissement(qs: QuerySet, user, *, field: str = 'etablissement') -> QuerySet:
    """Restreint au département de l'utilisateur sauf superuser."""
    if user.is_superuser:
        return qs
    etab = getattr(user, 'etablissement', None)
    if not etab:
        return qs.none()
    return qs.filter(**{field: etab})


def scope_courses(qs: QuerySet, user) -> QuerySet:
    if user.is_superuser:
        return qs
    etab = getattr(user, 'etablissement', None)
    if not etab:
        return qs.none()
    return qs.filter(
        Q(etablissement=etab)
        | Q(vehicule__etablissement=etab)
        | Q(demandeur__etablissement=etab)
        | Q(chauffeur__etablissement=etab)
    )


def scope_vehicules(qs: QuerySet, user) -> QuerySet:
    return scope_etablissement(qs, user, field='etablissement')


def filter_date_range(qs: QuerySet, field: str, date_debut: Optional[str], date_fin: Optional[str]) -> QuerySet:
    if date_debut:
        qs = qs.filter(**{f'{field}__gte': date_debut})
    if date_fin:
        qs = qs.filter(**{f'{field}__lte': date_fin})
    return qs


def filter_datetime_date(qs: QuerySet, field: str, date_debut: Optional[str], date_fin: Optional[str]) -> QuerySet:
    """Pour DateTimeField : compare sur la partie date."""
    if date_debut:
        qs = qs.filter(**{f'{field}__date__gte': date_debut})
    if date_fin:
        qs = qs.filter(**{f'{field}__date__lte': date_fin})
    return qs


def safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def l_per_100km(litres, distance_km) -> float:
    d = safe_float(distance_km)
    lit = safe_float(litres)
    if d <= 0 or lit <= 0:
        return 0.0
    return (lit * 100.0) / d


def cost_per_km(expenses, distance_km) -> float:
    d = safe_float(distance_km)
    e = safe_float(expenses)
    if d <= 0 or e <= 0:
        return 0.0
    return e / d


def rav_distance_and_litres(ravitaillements: Iterable) -> tuple[float, float, float]:
    """
    Retourne (distance_valide, litres_avec_delta_valide, litres_tous).
    Seuls les pleins avec Δkm > 0 contribuent à la distance et aux litres pour L/100.
    """
    distance = 0.0
    litres_valid = 0.0
    litres_all = 0.0
    for rav in ravitaillements:
        lit = safe_float(getattr(rav, 'litres', 0))
        litres_all += lit
        avant = getattr(rav, 'kilometrage_avant', None)
        apres = getattr(rav, 'kilometrage_apres', None)
        if avant is not None and apres is not None:
            delta = apres - avant
            if delta > 0:
                distance += float(delta)
                litres_valid += lit
    return distance, litres_valid, litres_all


def vehicle_expenses(vehicule_id, date_debut=None, date_fin=None) -> dict:
    """Carburant + entretien (terminés) pour un véhicule sur la période."""
    ravs = Ravitaillement.objects.filter(vehicule_id=vehicule_id)
    ents = Entretien.objects.filter(vehicule_id=vehicule_id, statut='termine')
    ravs = filter_datetime_date(ravs, 'date_ravitaillement', date_debut, date_fin)
    ents = filter_date_range(ents, 'date_entretien', date_debut, date_fin)

    rav_agg = ravs.aggregate(
        total=Coalesce(Sum('cout_total'), Decimal('0')),
        litres=Coalesce(Sum('litres'), Decimal('0')),
    )
    ent_agg = ents.aggregate(total=Coalesce(Sum('cout'), Decimal('0')))

    dist, litres_valid, _ = rav_distance_and_litres(ravs)
    carburant = safe_float(rav_agg['total'])
    entretien = safe_float(ent_agg['total'])
    litres = safe_float(rav_agg['litres'])
    return {
        'depenses_carburant': carburant,
        'depenses_entretien': entretien,
        'cout_total': carburant + entretien,
        'litres_consommes': litres,
        'litres_pour_conso': litres_valid,
        'distance_rav': dist,
        'conso_rav_l100': l_per_100km(litres_valid, dist),
    }


def mission_distance_for_vehicle(vehicule_id, date_debut=None, date_fin=None, chauffeur_id=None) -> float:
    qs = Course.objects.filter(
        vehicule_id=vehicule_id,
        statut='terminee',
        distance_parcourue__isnull=False,
        distance_parcourue__gt=0,
    )
    if chauffeur_id:
        qs = qs.filter(chauffeur_id=chauffeur_id)
    qs = filter_datetime_date(qs, 'date_depart', date_debut, date_fin)
    total = qs.aggregate(t=Coalesce(Sum('distance_parcourue'), 0))['t']
    return safe_float(total)


def score_conso_l100(conso: float) -> float:
    if conso <= 0:
        return 0.0
    if conso <= 6:
        return 100.0
    if conso <= 8:
        return 80.0
    if conso <= 10:
        return 60.0
    if conso <= 12:
        return 40.0
    return 20.0


def score_cout_km(cout_km: float) -> float:
    """Seuils en unité monétaire / km (FCFA ou $ selon données)."""
    if cout_km <= 0:
        return 0.0
    if cout_km <= 0.5:
        return 100.0
    if cout_km <= 1.0:
        return 80.0
    if cout_km <= 1.5:
        return 60.0
    if cout_km <= 2.0:
        return 40.0
    return 20.0


def build_chauffeur_evaluations(courses: QuerySet, date_debut=None, date_fin=None, notes_chauffeurs=None):
    """
    Agrège les courses terminées par chauffeur et calcule conso / coût / scores.
    Les dépenses véhicule sont attribuées au prorata de la distance du chauffeur.
    """
    from django.utils import timezone
    from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DurationField
    from django.db.models.functions import Coalesce

    notes_chauffeurs = notes_chauffeurs or {}
    courses = courses.filter(statut='terminee', chauffeur__isnull=False)

    stats = courses.values(
        'chauffeur__id',
        'chauffeur__first_name',
        'chauffeur__last_name',
        'chauffeur__date_joined',
    ).annotate(
        missions_terminees=Count('id'),
        distance_totale=Coalesce(Sum('distance_parcourue'), 0),
        duree_moyenne=Avg(ExpressionWrapper(
            F('date_fin') - F('date_depart'),
            output_field=DurationField()
        )),
    ).order_by('-missions_terminees')

    evaluations = []
    scores_data = []

    for row in stats:
        ch_id = row['chauffeur__id']
        ch_courses = courses.filter(chauffeur_id=ch_id)
        vehicle_ids = list(
            ch_courses.exclude(vehicule_id__isnull=True)
            .values_list('vehicule_id', flat=True)
            .distinct()
        )

        depenses_carburant = 0.0
        depenses_entretien = 0.0
        litres_consommes = 0.0
        vehicule_label = {'immatriculation': 'Plusieurs / N/A', 'marque': '', 'modele': ''}

        if len(vehicle_ids) == 1:
            v = Vehicule.objects.filter(id=vehicle_ids[0]).first()
            if v:
                vehicule_label = {
                    'immatriculation': v.immatriculation,
                    'marque': v.marque or '',
                    'modele': v.modele or '',
                }

        for vid in vehicle_ids:
            exp = vehicle_expenses(vid, date_debut, date_fin)
            dist_ch = mission_distance_for_vehicle(vid, date_debut, date_fin, chauffeur_id=ch_id)
            dist_all = mission_distance_for_vehicle(vid, date_debut, date_fin)
            share = (dist_ch / dist_all) if dist_all > 0 else (1.0 if dist_ch > 0 else 0.0)
            depenses_carburant += exp['depenses_carburant'] * share
            depenses_entretien += exp['depenses_entretien'] * share
            litres_consommes += exp['litres_consommes'] * share

        cout_total = depenses_carburant + depenses_entretien
        distance_totale = safe_float(row['distance_totale'])
        conso_moyenne = l_per_100km(litres_consommes, distance_totale)
        cout_km = cost_per_km(cout_total, distance_totale)

        jours_prestes = ch_courses.values('date_depart__date').distinct().count()
        date_joined = row['chauffeur__date_joined']
        anciennete = (timezone.now().date() - date_joined.date()).days if date_joined else 0
        missions_terminees = row['missions_terminees'] or 0
        distance_moyenne = distance_totale / missions_terminees if missions_terminees else 0
        missions_par_jour = missions_terminees / jours_prestes if jours_prestes else 0
        last_mission = ch_courses.order_by('-date_fin').first()
        date_mission = last_mission.date_fin if last_mission and last_mission.date_fin else None

        destinations = (
            ch_courses.values('destination')
            .annotate(count=Count('id'))
            .order_by('-count')[:3]
        )
        top_destinations = [f"{d['destination']} ({d['count']}x)" for d in destinations]

        score_productivite = min(100.0, (missions_par_jour / 2) * 100) if missions_par_jour > 0 else 0.0
        score_efficacite = score_conso_l100(conso_moyenne)
        score_rentabilite = score_cout_km(cout_km)
        score_regularite = min(100.0, (jours_prestes / 30) * 100) if jours_prestes > 0 else 0.0
        score_details = {
            'productivite': score_productivite,
            'efficacite': score_efficacite,
            'rentabilite': score_rentabilite,
            'regularite': score_regularite,
        }
        score_total = (
            score_productivite * 0.4
            + score_efficacite * 0.25
            + score_rentabilite * 0.20
            + score_regularite * 0.15
        )

        if score_total >= 85:
            classification, badge_class = 'Excellent', 'badge-success'
        elif score_total >= 70:
            classification, badge_class = 'Bon', 'badge-primary'
        elif score_total >= 55:
            classification, badge_class = 'Moyen', 'badge-warning'
        elif score_total >= 40:
            classification, badge_class = 'À améliorer', 'badge-danger'
        else:
            classification, badge_class = 'Critique', 'badge-dark'

        recommandations = []
        if score_details['productivite'] < 60:
            recommandations.append('Augmenter le nombre de missions par jour')
        if score_details['efficacite'] < 60:
            recommandations.append('Améliorer la conduite pour réduire la consommation')
        if score_details['rentabilite'] < 60:
            recommandations.append("Optimiser les coûts d'exploitation")
        if score_details['regularite'] < 60:
            recommandations.append("Améliorer l'assiduité")

        evaluations.append({
            'chauffeur': {
                'id': ch_id,
                'first_name': row['chauffeur__first_name'],
                'last_name': row['chauffeur__last_name'],
                'get_full_name': f"{row['chauffeur__first_name']} {row['chauffeur__last_name']}",
            },
            'vehicule': vehicule_label,
            'nb_courses': missions_terminees,
            'nb_courses_terminees': missions_terminees,
            'nb_jours_prestes': jours_prestes,
            'distance_totale': distance_totale,
            'anciennete': anciennete,
            'distance_moyenne': distance_moyenne,
            'missions_par_jour': missions_par_jour,
            'depenses_carburant': round(depenses_carburant, 2),
            'depenses_entretien': round(depenses_entretien, 2),
            'cout_total': round(cout_total, 2),
            'litres_consommes': round(litres_consommes, 2),
            'cout_km': round(cout_km, 4),
            'conso_moyenne': round(conso_moyenne, 2),
            'top_destinations': top_destinations,
            'notes': notes_chauffeurs.get(str(ch_id), ''),
            'date_mission': date_mission,
            'score_total': round(score_total, 1),
            'score_details': score_details,
            'classification': classification,
            'badge_class': badge_class,
            'recommandations': recommandations,
            'tendance': 'stable',
        })
        scores_data.append(score_total)

    return evaluations, scores_data


def vehicle_period_stats(vehicule, date_debut=None, date_fin=None) -> dict:
    """Stats cohérentes période pour un véhicule (missions date_depart + dépenses)."""
    courses = Course.objects.filter(vehicule=vehicule, statut='terminee')
    courses = filter_datetime_date(courses, 'date_depart', date_debut, date_fin)
    distance_missions = safe_float(
        courses.aggregate(t=Coalesce(Sum('distance_parcourue'), 0))['t']
    )
    exp = vehicle_expenses(vehicule.id, date_debut, date_fin)
    conso = l_per_100km(exp['litres_consommes'], distance_missions)
    # Préférer tank-to-tank si dispo
    if exp['distance_rav'] > 0 and exp['litres_pour_conso'] > 0:
        conso = exp['conso_rav_l100']
        distance_for_cost = exp['distance_rav']
    else:
        distance_for_cost = distance_missions
    return {
        'distance_missions': distance_missions,
        'distance_for_cost': distance_for_cost,
        **exp,
        'conso_moyenne': conso,
        'cout_km': cost_per_km(exp['cout_total'], distance_for_cost if distance_for_cost > 0 else distance_missions),
        'nb_missions': courses.count(),
    }
