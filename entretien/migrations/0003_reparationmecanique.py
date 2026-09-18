# Generated manually for ReparationMecanique

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import entretien.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_vehicule_chassis_nullable'),
        ('entretien', '0002_entretien_kilometrage_entretien_kilometrage_apres_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReparationMecanique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200, verbose_name='Problème (résumé)')),
                ('description', models.TextField(verbose_name='Description du problème')),
                ('garage', models.CharField(blank=True, default='', max_length=255, verbose_name='Garage / Prestataire')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente de réparation'), ('en_cours', 'En réparation'), ('repare', 'Réparé'), ('annule', 'Annulé')], default='en_attente', max_length=20)),
                ('devis_provisoire', models.DecimalField(decimal_places=2, help_text='Estimation avant réparation', max_digits=12, verbose_name='Devis provisoire ($)')),
                ('devis_confirme', models.DecimalField(blank=True, decimal_places=2, help_text='Montant réel pour le bilan comptable (requis à la clôture)', max_digits=12, null=True, verbose_name='Devis / coût confirmé ($)')),
                ('date_signalement', models.DateField(default=django.utils.timezone.localdate, verbose_name='Date du signalement')),
                ('date_debut_reparation', models.DateField(blank=True, null=True, verbose_name='Début réparation')),
                ('date_reparation', models.DateField(blank=True, null=True, verbose_name='Date de réparation terminée')),
                ('piece_justificative', models.FileField(blank=True, null=True, upload_to=entretien.models.piece_reparation_path, verbose_name='Facture / devis confirmé (PDF, JPG)')),
                ('commentaires', models.TextField(blank=True, default='')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('confirme_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reparations_confirmees', to=settings.AUTH_USER_MODEL)),
                ('createur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reparations_creees', to=settings.AUTH_USER_MODEL)),
                ('vehicule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reparations_mecaniques', to='core.vehicule')),
            ],
            options={
                'verbose_name': 'Réparation mécanique',
                'verbose_name_plural': 'Réparations mécaniques',
                'ordering': ['-date_signalement', '-id'],
            },
        ),
    ]
