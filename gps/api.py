import json
from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.api import _get_user_from_token
from core.models import Course
from .models import GPSPosition, GPSSettings
from .services import serialize_position, compute_mission_resume, gps_status_label


def _parse_timestamp(value):
    if not value:
        return timezone.now()
    if isinstance(value, (int, float)):
        # epoch ms or s
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.get_current_timezone())
    dt = parse_datetime(str(value))
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _normalize_point(raw):
    if not isinstance(raw, dict):
        return None, 'Point invalide'
    try:
        lat = float(raw.get('latitude'))
        lng = float(raw.get('longitude'))
    except (TypeError, ValueError):
        return None, 'latitude/longitude requis'
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None, 'Coordonnées hors limites'

    point = {
        'latitude': lat,
        'longitude': lng,
        'timestamp': _parse_timestamp(raw.get('timestamp') or raw.get('recorded_at')),
        'vitesse': _float_or_none(raw.get('vitesse') if raw.get('vitesse') is not None else raw.get('speed')),
        'heading': _float_or_none(raw.get('heading') if raw.get('heading') is not None else raw.get('direction')),
        'accuracy': _float_or_none(raw.get('accuracy') or raw.get('precision')),
        'kilometrage': _int_or_none(raw.get('kilometrage')),
        'event_type': raw.get('event_type') or 'ping',
        'battery_level': _int_or_none(raw.get('battery_level')),
        'client_id': str(raw.get('client_id') or raw.get('id') or '')[:64],
    }
    allowed = {c[0] for c in GPSPosition.EVENT_CHOICES}
    if point['event_type'] not in allowed:
        point['event_type'] = 'ping'
    return point, None


def _float_or_none(v):
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int_or_none(v):
    if v is None or v == '':
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _mission_allows_ingest(course, settings_obj):
    if course.statut == 'en_cours':
        return True
    # Sync offline juste après fin (fenêtre 2h) pour points tamponnés
    if course.statut == 'terminee' and course.date_fin:
        age = (timezone.now() - course.date_fin).total_seconds()
        return age <= 7200
    if not settings_obj.suivi_uniquement_mission_active and course.statut in ('validee', 'en_cours'):
        return True
    return False


@csrf_exempt
@require_http_methods(['POST'])
def api_chauffeur_gps_positions(request, course_id):
    """
    Reçoit une position ou un lot (offline sync).
    Body: { "positions": [ {...}, ... ] } ou un seul objet position.
    """
    user, err = _get_user_from_token(request, expected_roles=['chauffeur'])
    if err:
        return err

    try:
        course = Course.objects.select_related('vehicule', 'etablissement').get(
            id=course_id, chauffeur=user
        )
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mission introuvable'}, status=404)

    settings_obj = GPSSettings.get_for_etablissement(course.etablissement)
    if not settings_obj.actif:
        return JsonResponse({'success': False, 'error': 'Suivi GPS désactivé'}, status=403)

    if not _mission_allows_ingest(course, settings_obj):
        return JsonResponse({
            'success': False,
            'error': 'GPS autorisé uniquement pendant une mission active (ou sync post-mission récente)',
        }, status=400)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    raw_list = data.get('positions')
    if raw_list is None:
        raw_list = [data]
    if not isinstance(raw_list, list) or not raw_list:
        return JsonResponse({'success': False, 'error': 'Aucune position fournie'}, status=400)
    if len(raw_list) > 500:
        return JsonResponse({'success': False, 'error': 'Maximum 500 points par envoi'}, status=400)

    created = 0
    skipped = 0
    errors = []
    to_create = []

    for raw in raw_list:
        point, perror = _normalize_point(raw)
        if perror:
            errors.append(perror)
            continue
        if point['client_id']:
            exists = GPSPosition.objects.filter(
                course=course, client_id=point['client_id']
            ).exists()
            if exists:
                skipped += 1
                continue
        to_create.append(GPSPosition(
            course=course,
            chauffeur=user,
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
        ))

    if to_create:
        GPSPosition.objects.bulk_create(to_create, batch_size=200)
        created = len(to_create)

    return JsonResponse({
        'success': True,
        'created': created,
        'skipped': skipped,
        'errors': errors[:10],
        'intervalle_recommande': settings_obj.intervalle_secondes,
    })


@csrf_exempt
@require_http_methods(['GET'])
def api_mission_gps_track(request, course_id):
    """Piste GPS d'une mission (chauffeur propriétaire ou gestionnaire via token)."""
    user, err = _get_user_from_token(
        request, expected_roles=['chauffeur', 'dispatch', 'demandeur', 'admin']
    )
    if err:
        return err

    try:
        course = Course.objects.select_related('vehicule', 'chauffeur', 'etablissement').get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mission introuvable'}, status=404)

    if user.role == 'chauffeur' and course.chauffeur_id != user.id:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    if user.role == 'demandeur' and course.demandeur_id != user.id:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    if user.role == 'dispatch' and user.etablissement_id:
        if course.etablissement_id and course.etablissement_id != user.etablissement_id:
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)

    qs = GPSPosition.objects.filter(course=course).order_by('timestamp')
    since = request.GET.get('since')
    if since:
        dt = parse_datetime(since)
        if dt:
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            qs = qs.filter(timestamp__gt=dt)

    positions = [serialize_position(p) for p in qs[:5000]]
    last = qs.last()
    return JsonResponse({
        'success': True,
        'mission_id': course.id,
        'statut': course.statut,
        'gps_status': gps_status_label(last),
        'resume': compute_mission_resume(course),
        'positions': positions,
    })
