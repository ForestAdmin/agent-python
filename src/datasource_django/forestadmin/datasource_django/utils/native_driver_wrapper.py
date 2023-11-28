import os

from django.db.backends.utils import CursorDebugWrapper


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
