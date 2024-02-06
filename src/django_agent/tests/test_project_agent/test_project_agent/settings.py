import os

DEBUG = True
SECRET_KEY = "the_secret_key"
INSTALLED_APPS = [
    "forestadmin.django_agent",
    "test_app",
    "django.contrib.auth",
    "django.contrib.contenttypes",
]
ROOT_URLCONF = "test_project_agent.urls"

FOREST_ENV_SECRET = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
FOREST_AUTH_SECRET = "OfpssLrbgF3P4vHJTTpb"
FOREST_PREFIX = "/my_forest"
# FOREST_CUSTOMIZE_FUNCTION = "test_app.forest_admin.customize_agent"


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
    }
}
