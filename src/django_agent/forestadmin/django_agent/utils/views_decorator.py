try:
    from django.contrib.auth.decorators import login_not_required as no_django_login_required  # type: ignore
except ImportError:

    def no_django_login_required(fn):
        return fn
