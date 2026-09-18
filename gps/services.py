import math
from datetime import timedelta

from django.db.models import Max, Min, Count
from django.utils import timezone

from .models import GPSPosition


def haversine_km(lat1, lon1, lat2, lon2):
    """Distance en km entre deux points WGS84."""
    r = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlmb = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def positions_queryset(course):
    return GPSPosition.objects.filter(course=course).order_by('timestamp')


def compute_mission_resume(course):
    qs = positions_queryset(course)
    count = qs.count()
    if count == 0:
        return {
            'nb_points': 0,
            'distance_gps_km': 0.0,
            'duree_secondes': 0,
            'temps_arret_secondes': 0,
            'vitesse_max': None,
            'heure_premier_point': None,
            'heure_dernier_point': None,
            'distance_declaree_km': float(course.distance_parcourue or 0),
            'ecart_km': None,
        }

    points = list(qs.values(
        'latitude', 'longitude', 'timestamp', 'vitesse', 'event_type'
    ))
    distance = 0.0
    temps_arret = 0.0
    vitesse_max = None
    STOP_SPEED = 3.0  # km/h

    for i in range(1, len(points)):
        prev, cur = points[i - 1], points[i]
        distance += haversine_km(
            prev['latitude'], prev['longitude'],
            cur['latitude'], cur['longitude'],
        )
        dt = (cur['timestamp'] - prev['timestamp']).total_seconds()
        v = cur.get('vitesse')
        if v is not None:
            vitesse_max = max(vitesse_max or 0, float(v))
            if float(v) < STOP_SPEED and dt > 0:
                temps_arret += dt
        elif dt > 90:
            # Gap long sans vitesse → approximer arrêt partiel
            temps_arret += min(dt, 600)

    first_ts = points[0]['timestamp']
    last_ts = points[-1]['timestamp']
    duree = max(0, (last_ts - first_ts).total_seconds())
    distance_declaree = float(course.distance_parcourue or 0)
    ecart = abs(distance - distance_declaree) if distance_declaree else None

    return {
        'nb_points': count,
        'distance_gps_km': round(distance, 2),
        'duree_secondes': int(duree),
        'temps_arret_secondes': int(temps_arret),
        'vitesse_max': round(vitesse_max, 1) if vitesse_max is not None else None,
        'heure_premier_point': first_ts,
        'heure_dernier_point': last_ts,
        'distance_declaree_km': distance_declaree,
        'ecart_km': round(ecart, 2) if ecart is not None else None,
    }


def serialize_position(p):
    return {
        'id': p.id,
        'latitude': float(p.latitude),
        'longitude': float(p.longitude),
        'timestamp': p.timestamp.isoformat(),
        'vitesse': p.vitesse,
        'heading': p.heading,
        'accuracy': p.accuracy,
        'kilometrage': p.kilometrage,
        'event_type': p.event_type,
        'battery_level': p.battery_level,
    }


def last_position_age_seconds(position):
    if not position:
        return None
    return max(0, int((timezone.now() - position.timestamp).total_seconds()))


def gps_status_label(position, connected_threshold=90):
    if not position:
        return 'aucune'
    age = last_position_age_seconds(position)
    if age is not None and age <= connected_threshold:
        return 'connecte'
    return 'derniere_recue'


def haversine_m(lat1, lon1, lat2, lon2):
    return haversine_km(lat1, lon1, lat2, lon2) * 1000.0


def planned_points(course):
    """Points planifiés + rayon pour affichage carte / évaluation."""
    rayon = int(getattr(course, 'rayon_arrivee_metres', None) or 150)
    embarquement = None
    destination = None
    if course.embarquement_latitude is not None and course.embarquement_longitude is not None:
        embarquement = {
            'latitude': float(course.embarquement_latitude),
            'longitude': float(course.embarquement_longitude),
            'label': course.point_embarquement,
        }
    if course.destination_latitude is not None and course.destination_longitude is not None:
        destination = {
            'latitude': float(course.destination_latitude),
            'longitude': float(course.destination_longitude),
            'label': course.destination,
            'rayon_m': rayon,
        }
    return {
        'embarquement': embarquement,
        'destination': destination,
        'rayon_arrivee_metres': rayon,
        'distance_prevue_km': course.distance_prevue_km,
    }


def evaluate_mission(course, persist=True):
    """
    Évalue l'arrivée en zone destination, durée d'arrêt sur place,
    écart trajet réel vs distance prévue.
    """
    resume = compute_mission_resume(course)
    planned = planned_points(course)
    dest = planned['destination']
    rayon = planned['rayon_arrivee_metres']

    result = {
        **resume,
        'arrivee_ok': None,
        'heure_arrivee': None,
        'duree_arret_destination_s': 0,
        'ecart_trajet_km': None,
        'distance_prevue_km': planned['distance_prevue_km'],
        'rayon_arrivee_metres': rayon,
        'score': None,
        'has_destination_coords': bool(dest),
        'planned': planned,
    }

    if not dest:
        if persist:
            _persist_eval(course, result)
        return result

    qs = positions_queryset(course)
    points = list(qs.values('latitude', 'longitude', 'timestamp', 'vitesse'))
    if not points:
        result['arrivee_ok'] = False
        if persist:
            _persist_eval(course, result)
        return result

    STOP_SPEED = 3.0
    first_in_zone_ts = None
    duree_arret_zone = 0.0
    in_zone = False
    prev = None

    for cur in points:
        dist_m = haversine_m(
            cur['latitude'], cur['longitude'],
            dest['latitude'], dest['longitude'],
        )
        inside = dist_m <= rayon
        if inside and first_in_zone_ts is None:
            first_in_zone_ts = cur['timestamp']
        if prev is not None:
            dt = (cur['timestamp'] - prev['timestamp']).total_seconds()
            if dt > 0 and inside:
                v = cur.get('vitesse')
                if v is None or float(v) < STOP_SPEED:
                    duree_arret_zone += dt
        prev = cur
        in_zone = inside

    # Arrivée = au moins un point dans la zone
    result['arrivee_ok'] = first_in_zone_ts is not None
    result['heure_arrivee'] = first_in_zone_ts
    result['duree_arret_destination_s'] = int(duree_arret_zone)

    prevue = planned['distance_prevue_km']
    if prevue is not None and resume['distance_gps_km'] is not None:
        result['ecart_trajet_km'] = round(abs(float(resume['distance_gps_km']) - float(prevue)), 2)

    # Score 0-100
    score = 0
    if result['arrivee_ok']:
        score += 50
    if result['duree_arret_destination_s'] >= 60:
        score += 20
    elif result['duree_arret_destination_s'] > 0:
        score += 10
    if result['ecart_trajet_km'] is not None:
        if result['ecart_trajet_km'] <= max(0.5, 0.15 * float(prevue or 1)):
            score += 30
        elif result['ecart_trajet_km'] <= max(1.5, 0.35 * float(prevue or 1)):
            score += 15
    result['score'] = min(100, score)

    if persist:
        _persist_eval(course, result)
    return result


def _persist_eval(course, result):
    updates = {
        'eval_arrivee_ok': result.get('arrivee_ok'),
        'eval_heure_arrivee': result.get('heure_arrivee'),
        'eval_duree_arret_destination_s': result.get('duree_arret_destination_s') or 0,
        'eval_ecart_trajet_km': result.get('ecart_trajet_km'),
        'eval_score': result.get('score'),
    }
    if result.get('distance_prevue_km') is not None:
        updates['distance_prevue_km'] = result['distance_prevue_km']
    type(course).objects.filter(pk=course.pk).update(**updates)
    for k, v in updates.items():
        setattr(course, k, v)


def purge_expired_positions(retention_jours=365):
    cutoff = timezone.now() - timedelta(days=retention_jours)
    deleted, _ = GPSPosition.objects.filter(timestamp__lt=cutoff).delete()
    return deleted
