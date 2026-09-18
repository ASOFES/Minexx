# Align DB with model: allow null expiration dates for partial vehicle registration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_vehicule_accessoire'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicule',
            name='date_expiration_assurance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='date_expiration_controle_technique',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='date_expiration_vignette',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='date_expiration_stationnement',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='date_immatriculation',
            field=models.DateField(blank=True, null=True),
        ),
    ]
