from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response
from forestadmin.django_agent.utils.dispatcher import get_dispatcher_method


async def count(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["crud_related"]
    response = await resource.dispatch(convert_request(request, kwargs), "count")
    return convert_response(response)


async def csv(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["crud_related"]
    response = await resource.dispatch(convert_request(request, kwargs), "csv")
    return convert_response(response)


async def list_(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["crud_related"]
    action = get_dispatcher_method(request.method, False)
    response = await resource.dispatch(convert_request(request, kwargs), action)
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
list_.csrf_exempt = True
