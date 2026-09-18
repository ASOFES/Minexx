from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import json
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

# ============================================================================
# AUTHENTIFICATION
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    Authentification de l'utilisateur et génération du token JWT
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'message': 'Nom d\'utilisateur et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authentification
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Génération du token JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Connexion réussie',
                'data': {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'Nom d\'utilisateur ou mot de passe incorrect'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_verify_token(request):
    """
    Vérification de la validité d'un token JWT
    """
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return Response({
                'success': False,
                'message': 'Token requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérification du token (simplifiée pour l'exemple)
        # En production, utilisez jwt.decode() pour vérifier la signature
        try:
            # Ici vous devriez implémenter la vraie vérification JWT
            # Pour l'exemple, on simule une vérification réussie
            return Response({
                'success': True,
                'message': 'Token valide',
                'data': {
                    'valid': True,
                    'expires_in': 3600  # 1 heure
                }
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'success': False,
                'message': 'Token invalide ou expiré'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du token: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# CHAUFFEUR - GESTION DES MISSIONS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_chauffeur_missions(request):
    """
    Liste des missions assignées au chauffeur
    """
    try:
        # Récupération de l'ID du chauffeur depuis les paramètres ou headers
        chauffeur_id = request.GET.get('chauffeur_id')
        
        if not chauffeur_id:
            return Response({
                'success': False,
                'message': 'ID du chauffeur requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulation de données de missions
        missions = [
            {
                'id': 1,
                'titre': 'Livraison de marchandises',
                'description': 'Transport de colis de Kinshasa à Lubumbashi',
                'statut': 'en_attente',
                'date_creation': '2025-08-16T10:00:00Z',
                'date_debut': '2025-08-17T08:00:00Z',
                'date_fin': '2025-08-18T18:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Lubumbashi, RDC',
                'distance': 1500,  # km
                'prix': 250000,  # FCFA
            },
            {
                'id': 2,
                'titre': 'Transport de passagers',
                'description': 'Voyage Kinshasa - Matadi',
                'statut': 'en_cours',
                'date_creation': '2025-08-15T14:00:00Z',
                'date_debut': '2025-08-16T06:00:00Z',
                'date_fin': '2025-08-16T12:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Matadi, RDC',
                'distance': 350,  # km
                'prix': 75000,  # FCFA
            }
        ]
        
        return Response({
            'success': True,
            'message': 'Missions récupérées avec succès',
            'data': {
                'missions': missions,
                'total': len(missions)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des missions: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_chauffeur_demarrer(request, course_id):
    """
    Démarrage d'une mission par le chauffeur
    """
    try:
        data = json.loads(request.body)
        chauffeur_id = data.get('chauffeur_id')
        
        if not chauffeur_id:
            return Response({
                'success': False,
                'message': 'ID du chauffeur requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulation de la mise à jour du statut
        return Response({
            'success': True,
            'message': f'Mission {course_id} démarrée avec succès',
            'data': {
                'mission_id': course_id,
                'statut': 'en_cours',
                'date_debut': '2025-08-16T22:54:00Z',
                'chauffeur_id': chauffeur_id
            }
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la mission: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_chauffeur_terminer(request, course_id):
    """
    Finalisation d'une mission par le chauffeur
    """
    try:
        data = json.loads(request.body)
        chauffeur_id = data.get('chauffeur_id')
        
        if not chauffeur_id:
            return Response({
                'success': False,
                'message': 'ID du chauffeur requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulation de la finalisation
        return Response({
            'success': True,
            'message': f'Mission {course_id} terminée avec succès',
            'data': {
                'mission_id': course_id,
                'statut': 'terminee',
                'date_fin': '2025-08-16T22:54:00Z',
                'chauffeur_id': chauffeur_id
            }
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la finalisation de la mission: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# DEMANDEUR - GESTION DES DEMANDES
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_demandeur_demandes_list(request):
    """
    Liste des demandes créées par le demandeur
    """
    try:
        # Récupération de l'ID du demandeur depuis les paramètres
        demandeur_id = request.GET.get('demandeur_id')
        
        if not demandeur_id:
            return Response({
                'success': False,
                'message': 'ID du demandeur requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulation de données de demandes
        demandes = [
            {
                'id': 1,
                'titre': 'Transport de marchandises',
                'description': 'Besoin de transport pour colis fragile',
                'statut': 'en_attente',
                'date_creation': '2025-08-16T09:00:00Z',
                'date_souhaitee': '2025-08-18T08:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Lubumbashi, RDC',
                'type_transport': 'marchandises',
                'poids': 500,  # kg
                'volume': 2.5,  # m³
                'prix_propose': 200000,  # FCFA
                'chauffeur_assigne': None,
                'vehicule_assigne': None,
            },
            {
                'id': 2,
                'titre': 'Voyage personnel',
                'description': 'Déplacement Kinshasa - Matadi',
                'statut': 'en_cours',
                'date_creation': '2025-08-15T10:00:00Z',
                'date_souhaitee': '2025-08-16T06:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Matadi, RDC',
                'type_transport': 'passagers',
                'nombre_passagers': 3,
                'prix_propose': 70000,  # FCFA
                'chauffeur_assigne': 'Jean Dupont',
                'vehicule_assigne': 'Toyota Hiace - ABC123',
            }
        ]
        
        return Response({
            'success': True,
            'message': 'Demandes récupérées avec succès',
            'data': {
                'demandes': demandes,
                'total': len(demandes)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des demandes: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_demandeur_demandes_create(request):
    """
    Création d'une nouvelle demande de transport
    """
    try:
        data = json.loads(request.body)
        
        # Validation des champs requis
        required_fields = ['titre', 'description', 'lieu_depart', 'lieu_arrivee', 'type_transport']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'message': f'Champ requis manquant: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Simulation de la création
        nouvelle_demande = {
            'id': 3,  # ID généré automatiquement
            'titre': data['titre'],
            'description': data['description'],
            'statut': 'en_attente',
            'date_creation': '2025-08-16T22:54:00Z',
            'date_souhaitee': data.get('date_souhaitee'),
            'lieu_depart': data['lieu_depart'],
            'lieu_arrivee': data['lieu_arrivee'],
            'type_transport': data['type_transport'],
            'poids': data.get('poids'),
            'volume': data.get('volume'),
            'nombre_passagers': data.get('nombre_passagers'),
            'prix_propose': data.get('prix_propose'),
            'chauffeur_assigne': None,
            'vehicule_assigne': None,
        }
        
        return Response({
            'success': True,
            'message': 'Demande créée avec succès',
            'data': nouvelle_demande
        }, status=status.HTTP_201_CREATED)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de la création de la demande: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================================================
# DISPATCHER - GESTION DES DEMANDES
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def api_dispatch_demandes_list(request):
    """
    Liste de toutes les demandes pour le dispatcher
    """
    try:
        # Paramètres de filtrage
        statut = request.GET.get('statut')
        type_transport = request.GET.get('type_transport')
        
        # Simulation de données de demandes
        demandes = [
            {
                'id': 1,
                'titre': 'Transport de marchandises',
                'description': 'Besoin de transport pour colis fragile',
                'statut': 'en_attente',
                'date_creation': '2025-08-16T09:00:00Z',
                'date_souhaitee': '2025-08-18T08:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Lubumbashi, RDC',
                'type_transport': 'marchandises',
                'poids': 500,  # kg
                'volume': 2.5,  # m³
                'prix_propose': 200000,  # FCFA
                'demandeur': 'Marie Martin',
                'telephone': '+243 123 456 789',
                'chauffeur_assigne': None,
                'vehicule_assigne': None,
                'priorite': 'normale',
            },
            {
                'id': 2,
                'titre': 'Voyage personnel',
                'description': 'Déplacement Kinshasa - Matadi',
                'statut': 'en_cours',
                'date_creation': '2025-08-15T10:00:00Z',
                'date_souhaitee': '2025-08-16T06:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Matadi, RDC',
                'type_transport': 'passagers',
                'nombre_passagers': 3,
                'prix_propose': 70000,  # FCFA
                'demandeur': 'Pierre Durand',
                'telephone': '+243 987 654 321',
                'chauffeur_assigne': 'Jean Dupont',
                'vehicule_assigne': 'Toyota Hiace - ABC123',
                'priorite': 'elevee',
            },
            {
                'id': 3,
                'titre': 'Livraison express',
                'description': 'Transport urgent de documents',
                'statut': 'en_attente',
                'date_creation': '2025-08-16T15:00:00Z',
                'date_souhaitee': '2025-08-17T10:00:00Z',
                'lieu_depart': 'Kinshasa, RDC',
                'lieu_arrivee': 'Brazzaville, Congo',
                'type_transport': 'marchandises',
                'poids': 2,  # kg
                'volume': 0.1,  # m³
                'prix_propose': 150000,  # FCFA
                'demandeur': 'Société ABC',
                'telephone': '+242 111 222 333',
                'chauffeur_assigne': None,
                'vehicule_assigne': None,
                'priorite': 'urgente',
            }
        ]
        
        # Filtrage par statut
        if statut:
            demandes = [d for d in demandes if d['statut'] == statut]
        
        # Filtrage par type de transport
        if type_transport:
            demandes = [d for d in demandes if d['type_transport'] == type_transport]
        
        return Response({
            'success': True,
            'message': 'Demandes récupérées avec succès',
            'data': {
                'demandes': demandes,
                'total': len(demandes),
                'filtres_appliques': {
                    'statut': statut,
                    'type_transport': type_transport
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des demandes: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_dispatch_assigner(request, course_id):
    """
    Assignment d'une demande à un chauffeur et véhicule
    """
    try:
        data = json.loads(request.body)
        
        # Validation des champs requis
        required_fields = ['chauffeur_id', 'vehicule_id']
        for field in required_fields:
            if not data.get(field):
                return Response({
                    'success': False,
                    'message': f'Champ requis manquant: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        chauffeur_id = data['chauffeur_id']
        vehicule_id = data['vehicule_id']
        notes = data.get('notes', '')
        
        # Simulation de l'assignation
        assignation = {
            'demande_id': course_id,
            'chauffeur_id': chauffeur_id,
            'vehicule_id': vehicule_id,
            'date_assignation': '2025-08-16T22:54:00Z',
            'statut': 'assignee',
            'notes': notes,
            'dispatcher_id': data.get('dispatcher_id'),
        }
        
        return Response({
            'success': True,
            'message': f'Demande {course_id} assignée avec succès',
            'data': assignation
        }, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Erreur lors de l'assignation: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
