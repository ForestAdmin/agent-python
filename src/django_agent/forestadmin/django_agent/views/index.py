from django.db import transaction
from django.http import HttpRequest, HttpResponse
from forestadmin.django_agent.apps import DjangoAgentApp


@transaction.non_atomic_requests
async def index(request: HttpRequest):
    return HttpResponse(status=200)


@transaction.non_atomic_requests
async def scope_cache_invalidation(request: HttpRequest):
    DjangoAgentApp.get_agent()._permission_service.invalidate_cache("forest.scopes")
    return HttpResponse(status=204)
