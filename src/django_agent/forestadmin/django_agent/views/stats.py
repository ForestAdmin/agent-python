from django.db import transaction
from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response


@transaction.non_atomic_requests
async def stats(request: HttpRequest, **kwargs):
    resource = (await DjangoAgentApp.get_agent().get_resources())["stats"]
    response = await resource.dispatch(convert_request(request, kwargs))
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
stats.csrf_exempt = True
