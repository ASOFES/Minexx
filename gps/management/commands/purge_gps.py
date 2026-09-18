from django.core.management.base import BaseCommand

from gps.models import GPSSettings
from gps.services import purge_expired_positions


class Command(BaseCommand):
    help = 'Purge les positions GPS au-delà de la durée de rétention configurée'

    def handle(self, *args, **options):
        # Purge globale selon le max de rétention des settings (défaut 365)
        retentions = list(GPSSettings.objects.values_list('retention_jours', flat=True))
        days = min(retentions) if retentions else 365
        deleted = purge_expired_positions(days)
        self.stdout.write(self.style.SUCCESS(
            f'Positions GPS purgées: {deleted} (rétention {days} jours)'
        ))
