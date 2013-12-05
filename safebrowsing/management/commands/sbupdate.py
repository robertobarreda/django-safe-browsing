from django.core.management.base import BaseCommand, CommandError
from example.polls.models import Poll

class Command(BaseCommand):
    help = 'Updates the safe browsing db'

    def handle(self, *args, **options):
        pass
