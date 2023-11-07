from django.http import HttpRequest, HttpResponse


async def index(request: HttpRequest):
    return HttpResponse(status=200)
