from django.test import TestCase, Client
from django.urls import reverse
from core.models import Etablissement, Utilisateur, Vehicule
from .models import Ravitaillement

# Create your tests here.

class IsolationDepartementRavitaillementTest(TestCase):
    def setUp(self):
        self.dep1 = Etablissement.objects.create(nom="Département A")
        self.dep2 = Etablissement.objects.create(nom="Département B")
        self.user1 = Utilisateur.objects.create_user(username="user1", password="testpass1", etablissement=self.dep1, role="admin")
        self.user2 = Utilisateur.objects.create_user(username="user2", password="testpass2", etablissement=self.dep2, role="admin")
        self.vehicule1 = Vehicule.objects.create(immatriculation="AAA111", marque="Renault", modele="Clio", couleur="rouge", etablissement=self.dep1, numero_chassis="CHASSIS1", date_expiration_assurance="2030-01-01", date_expiration_controle_technique="2030-01-01", date_expiration_vignette="2030-01-01", date_expiration_stationnement="2030-01-01")
        self.vehicule2 = Vehicule.objects.create(immatriculation="BBB222", marque="Peugeot", modele="208", couleur="bleu", etablissement=self.dep2, numero_chassis="CHASSIS2", date_expiration_assurance="2030-01-01", date_expiration_controle_technique="2030-01-01", date_expiration_vignette="2030-01-01", date_expiration_stationnement="2030-01-01")
        self.ravitaillement1 = Ravitaillement.objects.create(vehicule=self.vehicule1, litres=20, cout_total=50, date_ravitaillement="2024-01-01", createur=self.user1)
        self.ravitaillement2 = Ravitaillement.objects.create(vehicule=self.vehicule2, litres=30, cout_total=70, date_ravitaillement="2024-01-02", createur=self.user2)

    def test_isolation_ravitaillements(self):
        client = Client()
        client.login(username="user1", password="testpass1")
        response = client.get(reverse("ravitaillement:liste_ravitaillements"))
        self.assertContains(response, "20")
        self.assertNotContains(response, "BBB222")
        self.assertContains(response, "AAA111")
        client.logout()
        client.login(username="user2", password="testpass2")
        response = client.get(reverse("ravitaillement:liste_ravitaillements"))
        self.assertContains(response, "30")
        self.assertNotContains(response, "AAA111")
