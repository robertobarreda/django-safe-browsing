from django.core.management.base import BaseCommand

from safebrowsing.managers import gsb_manager


class Command(BaseCommand):
    help = 'Deletes all items in the safe browsing db'

    def handle(self, *args, **options):
        gsb_manager.delete_all_data()
