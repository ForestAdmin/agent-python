from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response


async def hook(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["actions"]
    response = await resource.dispatch(convert_request(request, kwargs), "hook")
    return convert_response(response)


async def execute(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["actions"]
    response = await resource.dispatch(convert_request(request, kwargs), "execute")
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
hook.csrf_exempt = True
execute.csrf_exempt = True
