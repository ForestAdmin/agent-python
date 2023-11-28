from django.urls import include, path

urlpatterns = [
    path("", include("forestadmin.django_agent.urls")),
]
