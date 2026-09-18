# Generated manually for BudgetFlotte

from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0017_vehicule_chassis_nullable'),
        ('rapport', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetFlotte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('periode_type', models.CharField(choices=[('mensuel', 'Mensuel'), ('annuel', 'Annuel')], default='mensuel', max_length=10)),
                ('annee', models.PositiveIntegerField(verbose_name='Année')),
                ('mois', models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'), (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'), (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre')], null=True, verbose_name='Mois (si mensuel)')),
                ('budget_carburant', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('budget_entretien', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('budget_reparations', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('budget_divers', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14, verbose_name='Divers / imprévus ($)')),
                ('notes', models.TextField(blank=True, default='')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('createur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='budgets_crees', to=settings.AUTH_USER_MODEL)),
                ('etablissement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='budgets_flotte', to='core.etablissement', verbose_name='Département (vide = flotte globale)')),
            ],
            options={
                'verbose_name': 'Budget flotte',
                'verbose_name_plural': 'Budgets flotte',
                'ordering': ['-annee', '-mois', 'periode_type'],
            },
        ),
        migrations.AddConstraint(
            model_name='budgetflotte',
            constraint=models.UniqueConstraint(fields=('etablissement', 'periode_type', 'annee', 'mois'), name='uniq_budget_flotte_periode'),
        ),
    ]
