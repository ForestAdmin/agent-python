from app.forest_admin import customize_forest
from django.apps import AppConfig, apps
from forestadmin.django_agent.agent import DjangoAgent


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self) -> None:
        agent: DjangoAgent = apps.get_app_config("django_agent").get_agent()
        if agent:
            customize_forest(agent)
            agent.start()
