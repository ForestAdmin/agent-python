from django.db import transaction
from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response


@transaction.non_atomic_requests
async def chart_collection(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["collection_charts"]
    response = await resource.dispatch(convert_request(request, kwargs), "add")
    return convert_response(response)


@transaction.non_atomic_requests
async def chart_datasource(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["datasource_charts"]
    response = await resource.dispatch(convert_request(request, kwargs), "add")
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
chart_collection.csrf_exempt = True
chart_datasource.csrf_exempt = True
