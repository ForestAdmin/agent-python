from django.db import transaction
from django.http import HttpRequest, HttpResponse
from forestadmin.django_agent.apps import DjangoAgentApp
from forestadmin.django_agent.utils.views_decorator import no_django_login_required  # type: ignore


@no_django_login_required
@transaction.non_atomic_requests
async def index(request: HttpRequest):
    return HttpResponse(status=200)


@no_django_login_required
@transaction.non_atomic_requests
async def scope_cache_invalidation(request: HttpRequest):
    DjangoAgentApp.get_agent()._permission_service.invalidate_cache("forest.rendering")
    return HttpResponse(status=204)


# This is so ugly... But django.views.decorators.csrf.csrf_exempt is not asyncio ready
scope_cache_invalidation.csrf_exempt = True
