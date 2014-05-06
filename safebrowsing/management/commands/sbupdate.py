from django.core.management.base import BaseCommand

from safebrowsing.managers import gsb_manager


class Command(BaseCommand):
    help = 'Updates the safe browsing db'

    def handle(self, *args, **options):
        # get new chunks
        gsb_lists = ('goog-malware-shavar', 'googpub-phish-shavar')
        gsb_manager.download_data(gsb_lists)

        # zap outdated fullhash definitions (they are only good for 45m)
        gsb_manager.fullhash_delete_old()
