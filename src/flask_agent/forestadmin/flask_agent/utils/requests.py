from typing import Any, Dict, Union

from flask.wrappers import Request as FlaskRequest
from flask.wrappers import Response as FlaskResponse
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, RequestMethod, Response

HTTP_METHOD_MAPPING = {
    "GET": RequestMethod.GET,
    "POST": RequestMethod.POST,
    "PUT": RequestMethod.PUT,
    "DELETE": RequestMethod.DELETE,
}


def convert_request(flask_request: FlaskRequest):
    method = HTTP_METHOD_MAPPING[flask_request.method]
    query = {**flask_request.args}
    if flask_request.view_args:
        query.update(flask_request.view_args)
    kwargs: Dict[str, Any] = {"query": query, "headers": flask_request.headers}
    if method in [RequestMethod.POST, RequestMethod.PUT, RequestMethod.DELETE] and flask_request.get_data():
        kwargs["body"] = flask_request.json
    kwargs["client_ip"] = flask_request.headers.get("X-Forwarded-For", flask_request.remote_addr)

    return Request(method, **kwargs)


def convert_response(response: Union[Response, FileResponse]) -> FlaskResponse:
    if isinstance(response, FileResponse):
        flask_response = FlaskResponse(
            response.file,
            headers={
                "Content-Type": response.mimetype,
                "Content-Disposition": f"attachment; filename={response.name}",
                **response.headers,
            },
        )
    else:
        flask_response = FlaskResponse(response.body)
        for name, value in response.headers.items():
            flask_response.headers[name] = value
        flask_response.status = response.status
    return flask_response
