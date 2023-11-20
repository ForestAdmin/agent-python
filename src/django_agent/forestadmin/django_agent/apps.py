import asyncio
import importlib
import sys
from typing import Callable, Union

from django.apps import AppConfig
from django.conf import settings
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.django_agent.agent import DjangoAgent, create_agent


def is_launch_as_server() -> bool:
    is_manage_py = any(arg.casefold().endswith("manage.py") for arg in sys.argv)
    is_runserver = any(arg.casefold() == "runserver" for arg in sys.argv)
    return (is_manage_py and is_runserver) or (not is_manage_py)


class DjangoAgentApp(AppConfig):
    _DJANGO_AGENT: DjangoAgent = None
    name = "forestadmin.django_agent"

    @classmethod
    def get_agent(cls) -> DjangoAgent:
        if cls._DJANGO_AGENT is None:
            ForestLogger.log(
                "warning",
                "Trying to get the agent but it's not created. Did you have a forest error before? "
                "If not, this is no normal. "
                "May be you are trying to get the agent too early or during a manage command other than 'runserver' ?",
            )

        return cls._DJANGO_AGENT

    def ready(self):
        if is_launch_as_server():
            DjangoAgentApp._DJANGO_AGENT = create_agent()
            if not getattr(settings, "FOREST_DONT_AUTO_ADD_DJANGO_DATASOURCE", None):
                DjangoAgentApp._DJANGO_AGENT.add_datasource(DjangoDatasource())

            customize_fn = getattr(settings, "FOREST_CUSTOMIZE_FUNCTION", None)
            if customize_fn:
                self._call_user_customize_function(customize_fn)
            DjangoAgentApp._DJANGO_AGENT.start()

    def _call_user_customize_function(self, customize_fn: Union[str, Callable[[DjangoAgent], None]]):
        if isinstance(customize_fn, str):
            try:
                module_name, fn_name = customize_fn.rsplit(".", 1)
                module = importlib.import_module(module_name)
                customize_fn = getattr(module, fn_name)
            except Exception as exc:
                ForestLogger.log("error", f"cannot import {customize_fn} : {exc}. Quitting forest.")
                DjangoAgentApp._DJANGO_AGENT = None
                return

        if callable(customize_fn):
            try:
                if asyncio.iscoroutinefunction(customize_fn):
                    DjangoAgentApp._DJANGO_AGENT.loop.run_until_complete(customize_fn(DjangoAgentApp._DJANGO_AGENT))
                else:
                    customize_fn(DjangoAgentApp._DJANGO_AGENT)
            except Exception as exc:
                ForestLogger.log(
                    "error",
                    f'error executing "FOREST_CUSTOMIZE_FUNCTION" ({customize_fn}): {exc}. Quitting forest.',
                )
                DjangoAgentApp._DJANGO_AGENT = None
                return
