# Generated manually for budget documents + AchatDocumentBord

from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_vehicule_chassis_nullable'),
        ('rapport', '0002_budgetflotte'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetflotte',
            name='budget_documents_bord',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='Assurance, vignette, carte rose, contrôle technique, stationnement, etc.',
                max_digits=14,
                verbose_name='Budget achat documents de bord ($)',
            ),
        ),
        migrations.CreateModel(
            name='AchatDocumentBord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_document', models.CharField(choices=[('assurance', 'Assurance'), ('vignette', 'Vignette'), ('carte_rose', 'Carte rose'), ('controle_technique', 'Contrôle technique'), ('stationnement', 'Autorisation de stationnement'), ('autre', 'Autre document de bord')], max_length=30)),
                ('libelle', models.CharField(blank=True, default='', help_text='Précision optionnelle (ex. assureur, n° quittance)', max_length=200)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=14)),
                ('date_achat', models.DateField()),
                ('date_expiration', models.DateField(blank=True, null=True)),
                ('piece_jointe', models.FileField(blank=True, null=True, upload_to='documents_bord/achats/')),
                ('notes', models.TextField(blank=True, default='')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('createur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='achats_documents_bord', to=settings.AUTH_USER_MODEL)),
                ('etablissement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='achats_documents_bord', to='core.etablissement')),
                ('vehicule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achats_documents_bord', to='core.vehicule')),
            ],
            options={
                'verbose_name': 'Achat document de bord',
                'verbose_name_plural': 'Achats documents de bord',
                'ordering': ['-date_achat', '-id'],
            },
        ),
    ]
