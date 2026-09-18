# Generated manually for VehiculeAccessoire

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_course_destination_latitude_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VehiculeAccessoire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=120, verbose_name='Accessoire')),
                ('quantite', models.PositiveIntegerField(default=1, verbose_name='Quantité')),
                ('remarque', models.CharField(blank=True, default='', max_length=255, verbose_name='Remarque')),
                ('date_ajout', models.DateTimeField(auto_now_add=True)),
                ('vehicule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accessoires', to='core.vehicule')),
            ],
            options={
                'verbose_name': 'Accessoire véhicule',
                'verbose_name_plural': 'Accessoires véhicule',
                'ordering': ['nom'],
            },
        ),
    ]
