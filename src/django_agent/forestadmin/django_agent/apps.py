from corsheaders.signals import check_request_enabled
from django.apps import AppConfig

from .agent import DjangoAgent


def cors_allow_api_to_everyone(sender, request, **kwargs):
    return True


class DjangoAgentApp(AppConfig):
    _DJANGO_AGENT: DjangoAgent = None
    name = "forestadmin.django_agent"

    @classmethod
    def get_agent(cls):
        return cls._DJANGO_AGENT

    def ready(self):
        DjangoAgentApp._DJANGO_AGENT = DjangoAgent()
        check_request_enabled.connect(cors_allow_api_to_everyone)
