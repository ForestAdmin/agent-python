import json

from django.http import HttpRequest as DjangoRequest
from django.http import HttpResponse as DjangoResponse
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, RequestMethod, Response


def convert_request(django_request: DjangoRequest) -> Request:
    method = RequestMethod(django_request.method)
    # query_params = django_request.
    # TODO: enrich query_params with url collection & other ...
    query_params = {name: value for name, value in django_request.GET.items()}
    headers = {**django_request.headers}
    kwargs = {
        "headers": headers,
        "query": query_params,
        "client_ip": headers.get("X-Forwarded-For", django_request.META["REMOTE_ADDR"]),
    }
    if method in [RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE] and len(django_request.body):
        kwargs["body"] = json.loads(django_request.body.decode(django_request.encoding))
    return Request(method, **kwargs)


def convert_response(response: Response) -> DjangoResponse:
    if isinstance(response, FileResponse):
        pass
    else:
        return DjangoResponse(
            response.body,
            headers=response.headers,
            status=response.status,
        )
