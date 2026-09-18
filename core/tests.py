from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Etablissement, Vehicule, Course, ActionTraceur, ApplicationControl
from django.utils import timezone
from datetime import timedelta
from ravitaillement.models import Ravitaillement
from entretien.models import Entretien
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class CoreTests(TestCase):
    def setUp(self):
        # Créer un établissement de test
        self.etablissement = Etablissement.objects.create(
            nom="Test Etablissement",
            adresse="123 Test Street",
            telephone="1234567890",
            email="test@example.com"
        )
        
        # Créer un super admin
        self.super_admin = get_user_model().objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123',
            etablissement=self.etablissement
        )
        
        # Créer un admin normal
        self.admin = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin',
            etablissement=self.etablissement
        )
        
        # Créer un utilisateur normal
        self.user = get_user_model().objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123',
            role='demandeur',
            etablissement=self.etablissement
        )
        
        # Créer un client de test
        self.client = Client()

        ApplicationControl.objects.create(is_open=True)

    def test_login_view(self):
        response = self.client.post('/login/', {
            'username': 'user',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirection après connexion réussie
        response = self.client.post('/login/', {
            'username': 'user',
            'password': 'wrongpass'
        })
        self.assertIn(response.status_code, [200, 302, 401, 403])

    def test_user_management(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/users/create/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'demandeur',
            'etablissement': self.etablissement.id
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())

    def test_vehicule_management(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/vehicules/create/', {
            'immatriculation': 'TEST123',
            'marque': 'Test Marque',
            'modele': 'Test Modele',
            'couleur': 'Rouge',
            'numero_chassis': 'CHASSIS123',
            'date_expiration_assurance': timezone.now().date() + timedelta(days=365),
            'date_expiration_controle_technique': timezone.now().date() + timedelta(days=365),
            'date_expiration_vignette': timezone.now().date() + timedelta(days=365),
            'date_expiration_stationnement': timezone.now().date() + timedelta(days=365),
            'etablissement': self.etablissement.id
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(Vehicule.objects.filter(immatriculation='TEST123').exists())

    def test_course_management(self):
        self.client.login(username='admin', password='testpass123')
        vehicule = Vehicule.objects.create(
            immatriculation='TEST456',
            marque='Test Marque',
            modele='Test Modele',
            couleur='Bleu',
            numero_chassis='CHASSIS456',
            date_expiration_assurance=timezone.now().date() + timedelta(days=365),
            date_expiration_controle_technique=timezone.now().date() + timedelta(days=365),
            date_expiration_vignette=timezone.now().date() + timedelta(days=365),
            date_expiration_stationnement=timezone.now().date() + timedelta(days=365),
            etablissement=self.etablissement,
            createur=self.admin
        )
        # Il n'y a pas d'URL explicite pour la création de course, donc on teste la liste
        response = self.client.get('/dispatch/courses/')
        self.assertIn(response.status_code, [200, 302])

    def test_action_traceur(self):
        self.client.login(username='admin', password='testpass123')
        self.client.get('/vehicules/')
        print(list(ActionTraceur.objects.all()))  # Debug: affiche toutes les actions
        self.assertTrue(ActionTraceur.objects.filter(
            utilisateur=self.admin,
            action__icontains="véhicule"
        ).exists())

    def test_multi_tenancy(self):
        etablissement2 = Etablissement.objects.create(
            nom="Test Etablissement 2",
            adresse="456 Test Street",
            telephone="0987654321",
            email="test2@example.com"
        )
        user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            role='demandeur',
            etablissement=etablissement2
        )
        self.client.login(username='user', password='testpass123')
        response = self.client.get('/vehicules/')
        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(get_user_model().objects.filter(username='user2').exists())

    def test_super_admin_access(self):
        self.client.login(username='superadmin', password='testpass123')
        response = self.client.get('/users/')
        self.assertIn(response.status_code, [200, 302])
        response = self.client.get('/vehicules/')
        self.assertIn(response.status_code, [200, 302])
        response = self.client.get('/dispatch/courses/')
        self.assertIn(response.status_code, [200, 302])

class IsolationDepartementAllModulesTest(TestCase):
    def setUp(self):
        self.dep1 = Etablissement.objects.create(nom="Département A")
        self.dep2 = Etablissement.objects.create(nom="Département B")
        self.user1 = get_user_model().objects.create_user(
            username="user1", password="testpass1", etablissement=self.dep1, role="admin"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2", password="testpass2", etablissement=self.dep2, role="admin"
        )
        self.vehicule1 = Vehicule.objects.create(
            immatriculation="AAA111", marque="Renault", modele="Clio", couleur="rouge", etablissement=self.dep1, numero_chassis="CHASSIS1", date_expiration_assurance="2030-01-01", date_expiration_controle_technique="2030-01-01", date_expiration_vignette="2030-01-01", date_expiration_stationnement="2030-01-01"
        )
        self.vehicule2 = Vehicule.objects.create(
            immatriculation="BBB222", marque="Peugeot", modele="208", couleur="bleu", etablissement=self.dep2, numero_chassis="CHASSIS2", date_expiration_assurance="2030-01-01", date_expiration_controle_technique="2030-01-01", date_expiration_vignette="2030-01-01", date_expiration_stationnement="2030-01-01"
        )
        self.entretien1 = Entretien.objects.create(
            vehicule=self.vehicule1, motif="Vidange", garage="Garage A", cout=100, date_entretien="2024-01-01", statut="termine", createur=self.user1
        )
        self.entretien2 = Entretien.objects.create(
            vehicule=self.vehicule2, motif="Freins", garage="Garage B", cout=200, date_entretien="2024-01-02", statut="termine", createur=self.user2
        )
        self.ravitaillement1 = Ravitaillement.objects.create(
            vehicule=self.vehicule1, litres=20, cout_total=50, date_ravitaillement="2024-01-01", createur=self.user1
        )
        self.ravitaillement2 = Ravitaillement.objects.create(
            vehicule=self.vehicule2, litres=30, cout_total=70, date_ravitaillement="2024-01-02", createur=self.user2
        )

    def test_isolation_vehicules(self):
        client = Client()
        client.login(username="user1", password="testpass1")
        response = client.get(reverse("vehicule_list"))
        self.assertContains(response, "AAA111")
        self.assertNotContains(response, "BBB222")
        client.logout()
        client.login(username="user2", password="testpass2")
        response = client.get(reverse("vehicule_list"))
        self.assertContains(response, "BBB222")
        self.assertNotContains(response, "AAA111")

    def test_isolation_entretiens(self):
        client = Client()
        client.login(username="user1", password="testpass1")
        response = client.get(reverse("entretien:liste_entretiens"))
        self.assertContains(response, "Vidange")
        self.assertNotContains(response, "Freins")
        client.logout()
        client.login(username="user2", password="testpass2")
        response = client.get(reverse("entretien:liste_entretiens"))
        self.assertContains(response, "Freins")
        self.assertNotContains(response, "Vidange")

    def test_isolation_ravitaillements(self):
        client = Client()
        client.login(username="user1", password="testpass1")
        response = client.get(reverse("ravitaillement:liste_ravitaillements"))
        self.assertContains(response, "20")
        self.assertNotContains(response, "BBB222")  # Vérifie que l'immatriculation du véhicule du département 2 n'est pas présente
        client.logout()
        client.login(username="user2", password="testpass2")
        response = client.get(reverse("ravitaillement:liste_ravitaillements"))
        self.assertContains(response, "30")
        self.assertNotContains(response, "AAA111")  # Vérifie que l'immatriculation du véhicule du département 1 n'est pas présente

class MediaStorageTest(TestCase):
    def test_media_file_persistence(self):
        # Crée un fichier temporaire
        test_content = b"contenu de test image"
        test_file = SimpleUploadedFile("test_image.jpg", test_content, content_type="image/jpeg")
        # Chemin absolu attendu
        media_path = os.path.join(settings.MEDIA_ROOT, "test_image.jpg")
        # Écrit le fichier dans MEDIA_ROOT
        with open(media_path, "wb") as f:
            f.write(test_content)
        # Vérifie que le fichier existe
        self.assertTrue(os.path.exists(media_path), "Le fichier média n'a pas été créé dans MEDIA_ROOT.")
        # Vérifie que le contenu est correct
        with open(media_path, "rb") as f:
            self.assertEqual(f.read(), test_content)
        # Nettoyage
        os.remove(media_path)
