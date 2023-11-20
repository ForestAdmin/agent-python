from django.http import HttpRequest, HttpResponse
from forestadmin.django_agent.apps import DjangoAgentApp


async def index(request: HttpRequest):
    return HttpResponse(status=200)


async def scope_cache_invalidation(request: HttpRequest):
    DjangoAgentApp.get_agent()._permission_service.invalidate_cache("forest.scopes")
    return HttpResponse(status=204)
