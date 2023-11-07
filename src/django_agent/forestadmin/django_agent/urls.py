from django.urls import path

from .views import authentication, index

app_name = "django_agent"


urlpatterns = [
    # generic
    path("forest/", index.index, name="index"),
    # path("forest/scope-cache-invalidation", index.index),
    # authentication
    path("forest/authentication", authentication.authentication, name="authentication"),
    path("forest/authentication/callback", authentication.callback, name="authentication_callback"),
    # actions
    # crud
    # crud related
]
