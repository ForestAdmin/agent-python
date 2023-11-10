from django.apps import AppConfig

# from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.django_agent.agent import DjangoAgent


class DjangoAgentApp(AppConfig):
    _DJANGO_AGENT: DjangoAgent = None
    name = "forestadmin.django_agent"

    @classmethod
    def get_agent(cls):
        return cls._DJANGO_AGENT

    def ready(self):
        DjangoAgentApp._DJANGO_AGENT = DjangoAgent()
        # DjangoAgentApp._DJANGO_AGENT.add_datasource(DjangoDatasource())
