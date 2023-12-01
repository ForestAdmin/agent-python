import importlib
import os

from django.conf import settings
from django.db import DEFAULT_DB_ALIAS, models
from django.db.backends.utils import CursorDebugWrapper
from forestadmin.datasource_django.exception import DjangoNativeDriver


class NativeDriverWrapper:
    def __init__(self, connection):
        self.connection = connection

        self._old_dj_allow_async_unsafe = None
        self._cursor = None

    def __enter__(self) -> CursorDebugWrapper:
        self._old_dj_allow_async_unsafe = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        self._cursor = self.connection.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old_dj_allow_async_unsafe is None:
            del os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"]
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = self._old_dj_allow_async_unsafe

        self._cursor.close()


def get_db_for_native_driver(model: models.Model):
    db_name = DEFAULT_DB_ALIAS

    # if we use multiple databases with db router(s)
    if len(settings.DATABASES.keys()) > 1 and len(settings.DATABASE_ROUTERS) > 0:
        db_read = None
        db_write = None
        for router_str in settings.DATABASE_ROUTERS:
            module_name, class_name = router_str.rsplit(".", 1)
            router = getattr(importlib.import_module(module_name), class_name)()

            # forest_native_driver is an hint for user
            if db_read is None:
                db_read = router.db_for_read(model, forest_native_driver=True)
            if db_write is None:
                db_write = router.db_for_write(model, forest_native_driver=True)

            if db_read is not None and db_write is not None:
                break

        # because if it's not the same, we cannot choose which one to use
        if db_read != db_write:
            raise DjangoNativeDriver(
                "Cannot choose database between return db router. "
                f"Read database is '{db_read}', and write database is '{db_write}'."
            )
        db_name = db_read or DEFAULT_DB_ALIAS
    return db_name
