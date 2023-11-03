from django.core.management.base import BaseCommand


class PopulateDB(BaseCommand):
    help = "Create fake data for the database"

    # def add_arguments(self, parser):
    #     parser.add_argument("poll_ids", nargs="+", type=int)

    def handle(self, *args, **options):
        pass
        # TODO: write it
