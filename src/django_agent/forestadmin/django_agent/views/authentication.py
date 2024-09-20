from django.db import transaction
from django.http import HttpRequest
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.converter import convert_request, convert_response
from forestadmin.django_agent.utils.views_decorator import no_django_login_required  # type: ignore


@no_django_login_required
@transaction.non_atomic_requests
async def authentication(request: HttpRequest):
    resource = (await DjangoAgentApp.get_agent().get_resources())["authentication"]
    response = await resource.dispatch(convert_request(request), "authenticate")
    return convert_response(response)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
authentication.csrf_exempt = True


@no_django_login_required
@transaction.non_atomic_requests
async def callback(request: HttpRequest):
    resource = (await DjangoAgentApp.get_agent().get_resources())["authentication"]
    response = await resource.dispatch(convert_request(request), "callback")
    return convert_response(response)
