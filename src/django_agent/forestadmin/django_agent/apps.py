import asyncio
import importlib
import sys
from typing import Callable, Optional, Union

from django.apps import AppConfig
from django.conf import settings
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.django_agent.agent import DjangoAgent, create_agent


def is_launch_as_server() -> bool:
    is_manage_py = any(arg.casefold().endswith("manage.py") or arg.casefold().endswith("pytest") for arg in sys.argv)
    is_runserver = any(arg.casefold() == "runserver" for arg in sys.argv)
    return (is_manage_py and is_runserver) or (not is_manage_py)


def init_app_agent() -> Optional[DjangoAgent]:
    if not is_launch_as_server():
        return None
    agent = create_agent()
    if not hasattr(settings, "FOREST_AUTO_ADD_DJANGO_DATASOURCE") or settings.FOREST_AUTO_ADD_DJANGO_DATASOURCE:
        agent.add_datasource(DjangoDatasource())

    customize_fn = getattr(settings, "FOREST_CUSTOMIZE_FUNCTION", None)
    if customize_fn:
        agent = _call_user_customize_function(customize_fn, agent)

    if agent:
        agent.start()
    return agent


def _call_user_customize_function(customize_fn: Union[str, Callable[[DjangoAgent], None]], agent: DjangoAgent):
    if isinstance(customize_fn, str):
        try:
            module_name, fn_name = customize_fn.rsplit(".", 1)
            module = importlib.import_module(module_name)
            customize_fn = getattr(module, fn_name)
        except Exception as exc:
            ForestLogger.log("error", f"cannot import {customize_fn} : {exc}. Quitting forest.")
            return

    if callable(customize_fn):
        try:
            ret = customize_fn(agent)
            if asyncio.iscoroutine(ret):
                agent.loop.run_until_complete(ret)
        except Exception as exc:
            ForestLogger.log(
                "error",
                f'error executing "FOREST_CUSTOMIZE_FUNCTION" ({customize_fn}): {exc}. Quitting forest.',
            )
            return
    return agent


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
        DjangoAgentApp._DJANGO_AGENT = init_app_agent()
