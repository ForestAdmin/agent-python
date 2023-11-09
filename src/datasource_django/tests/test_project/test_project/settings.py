DEBUG = True

INSTALLED_APPS = ["tests.test_project.test_app"]
USE_TZ = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}
