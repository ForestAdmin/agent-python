from typing import Any, Dict, Union

from fastapi import Request as FastAPIRequest
from fastapi import Response as FastAPIResponse
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, RequestMethod, Response

HTTP_METHOD_MAPPING = {
    "GET": RequestMethod.GET,
    "POST": RequestMethod.POST,
    "PUT": RequestMethod.PUT,
    "DELETE": RequestMethod.DELETE,
}


async def convert_request(fastapi_request: FastAPIRequest):
    method = HTTP_METHOD_MAPPING[fastapi_request.method]
    query = {**fastapi_request.path_params}
    query.update(fastapi_request.query_params)
    kwargs: Dict[str, Any] = {"query": query, "headers": {k.title(): v for k, v in fastapi_request.headers.items()}}

    if method in [RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE] and await fastapi_request.body():
        kwargs["body"] = await fastapi_request.json()
    kwargs["client_ip"] = fastapi_request.headers.get("x-forwarded-for", getattr(fastapi_request.client, "host", None))

    return Request(method, **kwargs)


def convert_response(response: Union[Response, FileResponse]) -> FastAPIResponse:
    if isinstance(response, FileResponse):
        flask_response = FastAPIResponse(
            response.file,
            headers={
                "Content-Type": response.mimetype,
                "Content-Disposition": f"attachment; filename={response.name}",
                **response.headers,
            },
        )
    else:
        flask_response = FastAPIResponse(response.body, response.status, headers={**response.headers})
    return flask_response
