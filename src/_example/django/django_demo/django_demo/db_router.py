from django.db import models


class DBRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """

    route_app_labels = {"auth", "contenttypes"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model.__name__.startswith("Flask"):
            return "other"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model.__name__.startswith("Flask"):
            return "other"
        return "default"

    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        obj1_is_flask = obj1.__class__.__name__.startswith("Flask")
        obj2_is_flask = obj2.__class__.__name__.startswith("Flask")
        return (obj1_is_flask and obj2_is_flask) or (not obj1_is_flask and not obj2_is_flask)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        # return True
        # print("db, app_label, model_name, hints")
        # print(db, app_label, model_name, hints)
        allow_migrate = model_name is not None and (
            (db == "default" and not model_name.startswith("flask"))
            or (db == "other" and model_name.startswith("flask"))
        )
        # print(db, model_name, allow_migrate)
        return allow_migrate
