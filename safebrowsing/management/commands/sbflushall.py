import logging
from django.core.management.base import BaseCommand, CommandError
from safebrowsing.managers import manager

logger = logging.getLogger('safebrowsing')

class Command(BaseCommand):
    help = 'Deletes all items in the safe browsing db'

    def handle(self, *args, **options):
        manager.delete_all_data()
