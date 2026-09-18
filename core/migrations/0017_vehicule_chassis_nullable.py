# Allow empty chassis number for partial vehicle registration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_vehicule_dates_expiration_nullable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vehicule',
            name='numero_chassis',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='marque',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='modele',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='vehicule',
            name='couleur',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
    ]
