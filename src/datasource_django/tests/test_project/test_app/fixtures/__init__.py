import os

from django.conf import settings
from django.core.management import call_command


def create_db():
    pass
    # print(os.getcwd())
    # print(os.environ["DJANGO_SETTINGS_MODULE"])
    # print(os.path.abspath(os.path.join(settings.DB_PATH, "..")))
    print(settings.DATABASES)

    # call_command("shell", command="from django.conf import settings ; print(settings.DATABASES['default']['NAME'])")
    # call_command("shell", command="from django.conf import settings ; print(settings.DATABASES)")
    # call_command("showmigrations", settings=os.environ["DJANGO_SETTINGS_MODULE"])
    call_command("migrate")


def rm_db():
    pass
    if os.path.exists(settings.DB_PATH):
        os.remove(settings.DB_PATH)
    else:
        print("database does not exists")


def load_fixtures():
    base_dir = os.path.abspath(os.path.join(__file__, ".."))
    call_command("loaddata", os.path.join(base_dir, "person.json"))
    call_command("loaddata", os.path.join(base_dir, "book.json"))
