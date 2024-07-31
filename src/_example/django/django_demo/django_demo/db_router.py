from django.apps import apps
from django.db import models


class DBRouter:
    def db_for_read(self, model: models.Model, **hints):
        if model._meta.app_label == "big_ram":
            return "big_ram"
        if model.__name__.startswith("Flask"):
            return "other"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label == "big_ram":
            return "big_ram"
        if model.__name__.startswith("Flask"):
            return "other"
        return "default"

    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints):
        if obj1._meta.app_label == obj2._meta.app_label == "big_ram":
            return True
        obj1_is_flask = obj1.__class__.__name__.startswith("Flask")
        obj2_is_flask = obj2.__class__.__name__.startswith("Flask")
        return (obj1_is_flask and obj2_is_flask) or (not obj1_is_flask and not obj2_is_flask)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "big_ram":
            return False
        allow_migrate = model_name is not None and (
            (db == "default" and not model_name.startswith("flask"))
            or (db == "other" and model_name.startswith("flask"))
        )
        return allow_migrate
