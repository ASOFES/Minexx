from datetime import datetime, time, timedelta
import json

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_http_methods

from core.models import Utilisateur, Vehicule
from .access import (
    courses_queryset_for_user,
    get_course_for_gps_view,
    gps_manager_required,
    log_gps_access,
    user_can_manage_gps,
)
from .models import GPSPosition
from .services import (
    compute_mission_resume,
    evaluate_mission,
    gps_status_label,
    last_position_age_seconds,
    planned_points,
    serialize_position,
)


def _format_duration(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f'{h}h {m:02d}min'
    return f'{m} min {s:02d}s'


@gps_manager_required
def live_map(request):
    """Carte temps réel des missions en cours (établissement de l'utilisateur)."""
    log_gps_access(request.user, 'carte_live')
    return render(request, 'gps/live_map.html', {
        'page_title': 'Suivi GPS en direct',
    })


@gps_manager_required
@require_GET
def api_live_missions(request):
    qs = courses_queryset_for_user(request.user).filter(statut='en_cours')
    chauffeur_id = request.GET.get('chauffeur')
    vehicule_id = request.GET.get('vehicule')
    if chauffeur_id:
        qs = qs.filter(chauffeur_id=chauffeur_id)
    if vehicule_id:
        qs = qs.filter(vehicule_id=vehicule_id)

    missions = []
    for course in qs:
        last = (
            GPSPosition.objects.filter(course=course)
            .order_by('-timestamp')
            .first()
        )
        resume = compute_mission_resume(course)
        evaluation = evaluate_mission(course, persist=False)
        planned = planned_points(course)
        track = [
            serialize_position(p)
            for p in GPSPosition.objects.filter(course=course).order_by('timestamp')[:2000]
        ]
        missions.append({
            'id': course.id,
            'reference': f'Mission #{course.id}',
            'statut': course.statut,
            'destination': course.destination,
            'point_embarquement': course.point_embarquement,
            'date_depart': course.date_depart.isoformat() if course.date_depart else None,
            'chauffeur': (
                f'{course.chauffeur.get_full_name() or course.chauffeur.username}'
                if course.chauffeur_id else None
            ),
            'vehicule': (
                f'{course.vehicule.immatriculation}'
                if course.vehicule_id else None
            ),
            'last_position': serialize_position(last) if last else None,
            'gps_status': gps_status_label(last),
            'age_seconds': last_position_age_seconds(last),
            'distance_gps_km': resume['distance_gps_km'],
            'vitesse': last.vitesse if last else None,
            'track': track,
            'planned': planned,
            'evaluation': {
                'arrivee_ok': evaluation.get('arrivee_ok'),
                'score': evaluation.get('score'),
                'heure_arrivee': evaluation['heure_arrivee'].isoformat() if evaluation.get('heure_arrivee') else None,
            },
        })
    return JsonResponse({'success': True, 'missions': missions})


@login_required
def mission_detail(request, course_id):
    course = get_course_for_gps_view(request, course_id)
    log_gps_access(
        request.user,
        'historique_mission',
        course=course,
        details=f'Consultation GPS mission #{course.id}',
    )
    positions = list(GPSPosition.objects.filter(course=course).order_by('timestamp'))
    evaluation = evaluate_mission(course, persist=True)
    resume_display = {
        **evaluation,
        'duree_label': _format_duration(evaluation['duree_secondes']),
        'temps_arret_label': _format_duration(evaluation['temps_arret_secondes']),
        'duree_arret_destination_label': _format_duration(evaluation.get('duree_arret_destination_s') or 0),
        'heure_arrivee_label': (
            evaluation['heure_arrivee'].strftime('%d/%m/%Y %H:%M:%S')
            if evaluation.get('heure_arrivee') else None
        ),
    }
    positions_payload = [serialize_position(p) for p in positions]
    return render(request, 'gps/mission_detail.html', {
        'mission': course,
        'positions': positions,
        'positions_json': json.dumps(positions_payload),
        'planned_json': json.dumps(planned_points(course)),
        'resume': resume_display,
        'evaluation': resume_display,
        'can_manage': user_can_manage_gps(request.user),
    })


@login_required
@require_GET
def api_geocode(request):
    from .geocode import geocode_address
    q = request.GET.get('q', '')
    results = geocode_address(q)
    return JsonResponse({'success': True, 'results': results})


@gps_manager_required
def historique(request):
    """
    Historique des missions pour le suivi GPS.
    Affiche les courses validées / en cours / terminées de la période,
    même sans points GPS (démarrage web sans app mobile).
    """
    qs = courses_queryset_for_user(request.user).filter(
        statut__in=['validee', 'en_cours', 'terminee']
    ).order_by('-date_depart', '-date_validation', '-date_demande')

    date_from = parse_date(request.GET.get('date_from') or '')
    date_to = parse_date(request.GET.get('date_to') or '')
    chauffeur_id = request.GET.get('chauffeur')
    vehicule_id = request.GET.get('vehicule')
    mission_id = request.GET.get('mission')
    # Par défaut : aujourd'hui (évite le filtre « dernière heure » trop étroit)
    periode = request.GET.get('periode')
    if periode is None and not any(
        request.GET.get(k) for k in ('date_from', 'date_to', 'chauffeur', 'vehicule', 'mission')
    ):
        periode = 'aujourdhui'
    periode = periode or ''

    now = timezone.now()
    if periode == 'derniere_heure':
        since = now - timedelta(hours=1)
        qs = qs.filter(
            Q(date_depart__gte=since)
            | Q(date_fin__gte=since)
            | Q(date_validation__gte=since)
            | Q(positions_gps__timestamp__gte=since)
        )
    elif periode == 'aujourdhui':
        start = timezone.make_aware(
            datetime.combine(timezone.localdate(), time.min)
        )
        qs = qs.filter(
            Q(date_depart__gte=start)
            | Q(date_fin__gte=start)
            | Q(date_validation__gte=start)
            | Q(date_demande__date=timezone.localdate())
            | Q(positions_gps__timestamp__gte=start)
        )
    if date_from:
        qs = qs.filter(
            Q(date_depart__date__gte=date_from)
            | Q(date_fin__date__gte=date_from)
            | Q(date_validation__date__gte=date_from)
            | Q(date_demande__date__gte=date_from)
        )
    if date_to:
        qs = qs.filter(
            Q(date_depart__date__lte=date_to)
            | Q(date_fin__date__lte=date_to)
            | Q(date_validation__date__lte=date_to)
            | Q(date_demande__date__lte=date_to)
        )
    if chauffeur_id:
        qs = qs.filter(chauffeur_id=chauffeur_id)
    if vehicule_id:
        qs = qs.filter(vehicule_id=vehicule_id)
    if mission_id:
        qs = qs.filter(id=mission_id)

    qs = qs.distinct()[:100]
    missions = []
    for c in qs:
        r = compute_mission_resume(c)
        missions.append({
            'course': c,
            'resume': r,
            'duree_label': _format_duration(r['duree_secondes']),
            'sans_gps': r['nb_points'] == 0,
        })

    log_gps_access(request.user, 'liste_historique', details=request.GET.urlencode())

    etab = request.user.etablissement
    chauffeurs = Utilisateur.objects.filter(role='chauffeur', is_active=True)
    vehicules = Vehicule.objects.all()
    if etab and not request.user.is_superuser:
        chauffeurs = chauffeurs.filter(etablissement=etab)
        vehicules = vehicules.filter(etablissement=etab)

    return render(request, 'gps/historique.html', {
        'missions': missions,
        'chauffeurs': chauffeurs.order_by('last_name', 'first_name'),
        'vehicules': vehicules.order_by('immatriculation'),
        'filters': {
            'periode': periode,
            'date_from': request.GET.get('date_from') or '',
            'date_to': request.GET.get('date_to') or '',
            'chauffeur': chauffeur_id or '',
            'vehicule': vehicule_id or '',
            'mission': mission_id or '',
        },
    })


@login_required
@require_GET
def api_mission_positions(request, course_id):
    course = get_course_for_gps_view(request, course_id)
    qs = GPSPosition.objects.filter(course=course).order_by('timestamp')
    return JsonResponse({
        'success': True,
        'mission_id': course.id,
        'statut': course.statut,
        'resume': compute_mission_resume(course),
        'positions': [serialize_position(p) for p in qs[:5000]],
    })


@login_required
@require_http_methods(['POST'])
def web_ping(request, course_id):
    """Envoi GPS depuis le navigateur chauffeur (mission en_cours)."""
    import json
    from .api import _normalize_point, _mission_allows_ingest
    from .models import GPSSettings

    course = get_course_for_gps_view(request, course_id)
    if request.user.role == 'chauffeur' and course.chauffeur_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
    if request.user.role not in ('chauffeur', 'admin') and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)

    settings_obj = GPSSettings.get_for_etablissement(course.etablissement)
    if not settings_obj.actif or not _mission_allows_ingest(course, settings_obj):
        return JsonResponse({'success': False, 'error': 'Suivi GPS non actif pour cette mission'}, status=400)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    point, perror = _normalize_point(data)
    if perror:
        return JsonResponse({'success': False, 'error': perror}, status=400)

    if point['client_id'] and GPSPosition.objects.filter(course=course, client_id=point['client_id']).exists():
        return JsonResponse({'success': True, 'created': 0, 'skipped': 1})

    GPSPosition.objects.create(
        course=course,
        chauffeur=course.chauffeur or request.user,
        vehicule=course.vehicule,
        latitude=point['latitude'],
        longitude=point['longitude'],
        timestamp=point['timestamp'],
        vitesse=point['vitesse'],
        heading=point['heading'],
        accuracy=point['accuracy'],
        kilometrage=point['kilometrage'],
        event_type=point['event_type'],
        battery_level=point['battery_level'],
        client_id=point['client_id'],
    )
    return JsonResponse({
        'success': True,
        'created': 1,
        'intervalle_recommande': settings_obj.intervalle_secondes,
    })
