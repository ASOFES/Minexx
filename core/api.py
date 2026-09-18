from django.contrib.auth import authenticate
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Utilisateur, Course, Vehicule
from suivi.models import SuiviVehicule

# Tokens API signés (TimestampSigner via dumps/loads), expiration 7 jours
API_TOKEN_SALT = 'minexx-api-auth'
API_TOKEN_MAX_AGE = 60 * 60 * 24 * 7
ACTIVE_MISSION_STATUSES = ['validee', 'en_cours']


def _create_api_token(user):
    """Génère un token signé et daté (non falsifiable)."""
    return signing.dumps(
        {'uid': user.id, 'role': user.role, 'username': user.username},
        salt=API_TOKEN_SALT,
    )


def _get_user_from_token(request, expected_roles=None):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, JsonResponse(
            {'success': False, 'error': "Token d'authentification requis"},
            status=401,
        )
    token = auth_header.split(' ', 1)[1].strip()
    try:
        payload = signing.loads(token, salt=API_TOKEN_SALT, max_age=API_TOKEN_MAX_AGE)
    except signing.SignatureExpired:
        return None, JsonResponse(
            {'success': False, 'error': 'Token expiré'},
            status=401,
        )
    except signing.BadSignature:
        return None, JsonResponse(
            {'success': False, 'error': 'Token invalide'},
            status=401,
        )

    try:
        user = Utilisateur.objects.get(
            id=payload.get('uid'),
            username=payload.get('username'),
            is_active=True,
        )
    except Utilisateur.DoesNotExist:
        return None, JsonResponse(
            {'success': False, 'error': 'Token invalide ou expiré'},
            status=401,
        )

    if user.role != payload.get('role'):
        return None, JsonResponse(
            {'success': False, 'error': 'Token invalide'},
            status=401,
        )

    if expected_roles and user.role not in expected_roles:
        return None, JsonResponse(
            {'success': False, 'error': 'Accès non autorisé'},
            status=403,
        )
    return user, None


def _user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'role': user.role,
        'telephone': user.telephone,
        'etablissement': user.etablissement.nom if user.etablissement else None,
    }


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Endpoint API pour la connexion des applications mobiles"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Nom d\'utilisateur et mot de passe requis'
            }, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            if user.role in ['chauffeur', 'dispatch', 'demandeur']:
                return JsonResponse({
                    'success': True,
                    'token': _create_api_token(user),
                    'user': _user_payload(user),
                })
            return JsonResponse({
                'success': False,
                'error': "Accès non autorisé. Rôle requis: chauffeur, dispatch ou demandeur"
            }, status=403)

        return JsonResponse({
            'success': False,
            'error': 'Nom d\'utilisateur ou mot de passe incorrect'
        }, status=401)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format JSON invalide'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


# -------------------- DEMANDEUR --------------------

@csrf_exempt
@require_http_methods(["POST"])
def api_demandeur_demandes_create(request):
    """Créer une demande de mission (Course) par un demandeur"""
    user, err = _get_user_from_token(request, expected_roles=['demandeur'])
    if err:
        return err
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    required = ['point_embarquement', 'destination', 'motif', 'nombre_passagers']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return JsonResponse(
            {'success': False, 'error': f"Champs manquants: {', '.join(missing)}"},
            status=400,
        )

    course = Course.objects.create(
        demandeur=user,
        etablissement=user.etablissement,
        point_embarquement=data['point_embarquement'],
        destination=data['destination'],
        motif=data['motif'],
        nombre_passagers=int(data.get('nombre_passagers', 1)),
        date_souhaitee=(
            timezone.datetime.fromisoformat(data['date_souhaitee'])
            if data.get('date_souhaitee') else None
        ),
        priorite=data.get('priorite', 'important'),
        statut='en_attente',
    )
    return JsonResponse({'success': True, 'demande_id': course.id})


@csrf_exempt
@require_http_methods(["GET"])
def api_demandeur_demandes_list(request):
    """Lister les demandes d'un demandeur"""
    user, err = _get_user_from_token(request, expected_roles=['demandeur'])
    if err:
        return err
    qs = Course.objects.filter(demandeur=user).order_by('-date_demande')
    result = [{
        'id': c.id,
        'point_embarquement': c.point_embarquement,
        'destination': c.destination,
        'motif': c.motif,
        'nombre_passagers': c.nombre_passagers,
        'date_demande': c.date_demande.isoformat() if c.date_demande else None,
        'date_souhaitee': c.date_souhaitee.isoformat() if c.date_souhaitee else None,
        'statut': c.statut,
        'priorite': c.priorite,
        'chauffeur': c.chauffeur.username if c.chauffeur_id else None,
        'vehicule': c.vehicule.immatriculation if c.vehicule_id else None,
    } for c in qs]
    return JsonResponse({'success': True, 'demandes': result})


# -------------------- DISPATCH --------------------

@csrf_exempt
@require_http_methods(["GET"])
def api_dispatch_demandes_list(request):
    """Liste des demandes filtrables par statut pour le dispatcher"""
    user, err = _get_user_from_token(request, expected_roles=['dispatch'])
    if err:
        return err
    statut = request.GET.get('statut')
    qs = Course.objects.all().order_by('-date_demande')
    if statut:
        qs = qs.filter(statut=statut)
    data = [{
        'id': c.id,
        'demandeur': c.demandeur.username if c.demandeur_id else None,
        'point_embarquement': c.point_embarquement,
        'destination': c.destination,
        'motif': c.motif,
        'nombre_passagers': c.nombre_passagers,
        'date_demande': c.date_demande.isoformat() if c.date_demande else None,
        'date_souhaitee': c.date_souhaitee.isoformat() if c.date_souhaitee else None,
        'statut': c.statut,
        'priorite': c.priorite,
        'chauffeur': c.chauffeur.username if c.chauffeur_id else None,
        'vehicule': c.vehicule.immatriculation if c.vehicule_id else None,
    } for c in qs]
    return JsonResponse({'success': True, 'demandes': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_dispatch_assigner(request, course_id):
    """Valider/refuser et assigner une demande: chauffeur + véhicule"""
    user, err = _get_user_from_token(request, expected_roles=['dispatch'])
    if err:
        return err
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    action = data.get('action', 'valider')  # valider | refuser

    try:
        with transaction.atomic():
            try:
                course = Course.objects.select_for_update().get(id=course_id)
            except Course.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Demande introuvable'}, status=404)

            if course.statut != 'en_attente':
                return JsonResponse({
                    'success': False,
                    'error': f"Cette demande a déjà été traitée (statut: {course.statut})",
                }, status=400)

            if action == 'refuser':
                course.statut = 'refusee'
                course.dispatcher = user
                course.save()
                return JsonResponse({'success': True, 'statut': course.statut})

            chauffeur_id = data.get('chauffeur_id')
            vehicule_id = data.get('vehicule_id')
            if not chauffeur_id or not vehicule_id:
                return JsonResponse({
                    'success': False,
                    'error': 'chauffeur_id et vehicule_id requis',
                }, status=400)

            try:
                chauffeur = Utilisateur.objects.select_for_update().get(
                    id=chauffeur_id, role='chauffeur', is_active=True
                )
                vehicule = Vehicule.objects.select_for_update().get(id=vehicule_id)
            except Utilisateur.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Chauffeur invalide'}, status=400)
            except Vehicule.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Véhicule invalide'}, status=400)

            # Respecter l'établissement de la demande
            if course.etablissement_id:
                if chauffeur.etablissement_id and chauffeur.etablissement_id != course.etablissement_id:
                    return JsonResponse({
                        'success': False,
                        'error': "Le chauffeur n'appartient pas à l'établissement de la demande",
                    }, status=400)
                if vehicule.etablissement_id and vehicule.etablissement_id != course.etablissement_id:
                    return JsonResponse({
                        'success': False,
                        'error': "Le véhicule n'appartient pas à l'établissement de la demande",
                    }, status=400)

            if not vehicule.est_disponible():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce véhicule n\'est pas disponible (mission active ou bloqué sécurité)',
                }, status=400)

            if Course.objects.filter(
                chauffeur=chauffeur, statut__in=ACTIVE_MISSION_STATUSES
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce chauffeur a déjà une mission active',
                }, status=400)

            course.chauffeur = chauffeur
            course.vehicule = vehicule
            course.dispatcher = user
            course.statut = 'validee'
            course.date_validation = timezone.now()
            course.save()
            return JsonResponse({'success': True, 'statut': course.statut})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# -------------------- CHAUFFEUR actions --------------------

@csrf_exempt
@require_http_methods(["POST"])
def api_chauffeur_demarrer(request, course_id):
    user, err = _get_user_from_token(request, expected_roles=['chauffeur'])
    if err:
        return err
    try:
        course = Course.objects.get(id=course_id, chauffeur=user)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mission introuvable'}, status=404)

    if course.statut != 'validee':
        return JsonResponse({
            'success': False,
            'error': 'La mission doit être validée avant de démarrer',
        }, status=400)

    if course.vehicule_id and course.vehicule.est_bloque_par_securite():
        return JsonResponse({
            'success': False,
            'error': 'Véhicule bloqué par la sécurité (checklist ou incident)',
        }, status=400)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    km_depart = data.get('kilometrage_depart')
    if km_depart is None:
        return JsonResponse({'success': False, 'error': 'kilometrage_depart requis'}, status=400)

    try:
        course.kilometrage_depart = int(km_depart)
        course.statut = 'en_cours'
        course.date_depart = timezone.now()
        course.full_clean()
        course.save()
    except (ValidationError, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': True, 'statut': course.statut})


@csrf_exempt
@require_http_methods(["POST"])
def api_chauffeur_terminer(request, course_id):
    user, err = _get_user_from_token(request, expected_roles=['chauffeur'])
    if err:
        return err
    try:
        course = Course.objects.get(id=course_id, chauffeur=user)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mission introuvable'}, status=404)

    if course.statut != 'en_cours':
        return JsonResponse({
            'success': False,
            'error': 'La mission doit être en cours pour être terminée',
        }, status=400)

    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)

    km_fin = data.get('kilometrage_fin')
    if km_fin is None:
        return JsonResponse({'success': False, 'error': 'kilometrage_fin requis'}, status=400)

    try:
        course.kilometrage_fin = int(km_fin)
        course.statut = 'terminee'
        course.date_fin = timezone.now()
        course.full_clean()
        course.save()
    except (ValidationError, ValueError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    try:
        from gps.services import evaluate_mission
        evaluate_mission(course, persist=True)
    except Exception:
        pass

    # Synchroniser le kilométrage même si la distance est 0
    if course.vehicule_id and course.kilometrage_fin is not None:
        veh = course.vehicule
        veh.kilometrage_actuel = max(veh.kilometrage_actuel or 0, course.kilometrage_fin)
        veh.save(update_fields=['kilometrage_actuel'])
        if course.distance_parcourue is not None:
            SuiviVehicule.mettre_a_jour_suivi(
                veh, timezone.now().date(), course.distance_parcourue
            )

    return JsonResponse({
        'success': True,
        'statut': course.statut,
        'distance_parcourue': course.distance_parcourue,
    })


@csrf_exempt
@require_http_methods(["GET"])
def api_verify_token(request):
    """Endpoint API pour vérifier la validité d'un token"""
    user, err = _get_user_from_token(
        request, expected_roles=['chauffeur', 'dispatch', 'demandeur']
    )
    if err:
        return err
    return JsonResponse({'success': True, 'user': _user_payload(user)})


@csrf_exempt
@require_http_methods(["POST"])
def api_chauffeur_gps_proxy(request, course_id):
    from gps.api import api_chauffeur_gps_positions
    return api_chauffeur_gps_positions(request, course_id)


@csrf_exempt
@require_http_methods(["GET"])
def api_chauffeur_gps_track_proxy(request, course_id):
    from gps.api import api_mission_gps_track
    return api_mission_gps_track(request, course_id)


@csrf_exempt
@require_http_methods(["GET"])
def api_chauffeur_missions(request):
    """Endpoint API pour récupérer les missions d'un chauffeur (assignées)"""
    user, err = _get_user_from_token(request, expected_roles=['chauffeur'])
    if err:
        return err

    courses = Course.objects.filter(chauffeur=user).order_by('-date_demande')
    missions = []
    for c in courses:
        missions.append({
            'id': c.id,
            'demandeur': (
                f"{c.demandeur.first_name} {c.demandeur.last_name}"
                if c.demandeur_id else None
            ),
            'point_embarquement': c.point_embarquement,
            'destination': c.destination,
            'motif': c.motif,
            'nombre_passagers': c.nombre_passagers,
            'date_demande': c.date_demande.isoformat() if c.date_demande else None,
            'date_souhaitee': c.date_souhaitee.isoformat() if c.date_souhaitee else None,
            'statut': c.statut,
            'priorite': c.priorite,
            'vehicule_immatriculation': c.vehicule.immatriculation if c.vehicule_id else None,
            'vehicule_marque': c.vehicule.marque if c.vehicule_id else None,
            'vehicule_modele': c.vehicule.modele if c.vehicule_id else None,
            'kilometrage_depart': c.kilometrage_depart,
            'kilometrage_fin': c.kilometrage_fin,
            'distance_parcourue': c.distance_parcourue,
        })
    return JsonResponse({'success': True, 'missions': missions})
