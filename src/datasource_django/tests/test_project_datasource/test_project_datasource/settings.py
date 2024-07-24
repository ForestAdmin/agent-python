import os

DEBUG = True

INSTALLED_APPS = [
    "test_app",
    "django.contrib.auth",
    "django.contrib.contenttypes",
]
DB_PATH = os.path.abspath(os.path.join(__file__, "..", "..", "test_db.sqlite"))
USE_TZ = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_PATH,
        # "TEST_NAME": DB_PATH,
        # "OPTIONS": {
        #     "timeout": 2000,
        #     # "init_command": "SET storage_engine=MEMORY",
        # },
        "TEST": {"NAME": DB_PATH},
    },
    "other": {
        "ENGINE": "django.db.backends.sqlite3",
        # "NAME": ":memory:",
        "NAME": os.path.abspath(os.path.join(__file__, "..", "..", "test_db.sqlite")),
        "TEST": {"NAME": ":memory:"},
        # "TEST": {"NAME": os.path.abspath(os.path.join(__file__, "..", "..", "other_test_db.sqlite"))},
    },
}
