from asgiref.sync import async_to_sync
from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response


@async_to_sync
async def capabilities(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["capabilities"]
    response = await resource.dispatch(convert_request(request, kwargs), "capabilities")
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
capabilities.csrf_exempt = True
