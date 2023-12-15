import json
from typing import Literal

from forestadmin.agent_toolkit.resources.collections.decorators import ip_white_list
from forestadmin.agent_toolkit.resources.ip_white_list_resource import IpWhitelistResource
from forestadmin.agent_toolkit.resources.security.exceptions import AuthenticationException, OpenIdException
from forestadmin.agent_toolkit.utils.authentication import ClientFactory, CustomClientOic
from forestadmin.agent_toolkit.utils.context import Request, Response
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.agent_toolkit.utils.token import build_jwt

LiteralMethod = Literal["authenticate", "callback"]


class Authentication(IpWhitelistResource):
    @ip_white_list
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            return await method(request)
        except Exception as exc:
            return self._handle_error(method_name, request, exc)

    async def authenticate(self, request: Request) -> Response:
        if not request.body:
            raise AuthenticationException("renderingId is missing in the request's body")
        try:
            rendering_id = int(request.body["renderingId"])
        except KeyError:
            raise AuthenticationException("renderingId is missing in the request's body")
        except ValueError:
            raise AuthenticationException("renderingId should be an integer")

        client: CustomClientOic = await ClientFactory.build(self.option)
        authorization_url = client.get_authorization_url(json.dumps({"renderingId": rendering_id}))

        return Response(
            status=200,
            body=json.dumps({"authorizationUrl": authorization_url}),
            headers={"content_type": "application/json"},
        )

    async def callback(self, request: Request) -> Response:
        client: CustomClientOic = await ClientFactory.build(self.option)
        if not request.query:
            raise AuthenticationException("`state`should be sent to the callback endpoint")
        try:
            state = json.loads(request.query["state"])
        except KeyError:
            raise AuthenticationException("`state`should be sent to the callback endpoint")
        except ValueError:
            raise AuthenticationException("state should be a json")

        try:
            rendering_id = int(state["renderingId"])
        except KeyError:
            raise AuthenticationException("renderingId is missing in the callback state")
        except ValueError:
            raise AuthenticationException("renderingId should be an integer")

        authorization_response = client.get_parsed_response(request.query)
        access_token_response = client.get_access_token(authorization_response)
        rendering_authorization_response = await ForestHttpApi.get_rendering_authorization(
            rendering_id, access_token_response["access_token"], self.option
        )
        user = rendering_authorization_response["data"]["attributes"]

        token, body = build_jwt(
            {
                "id": rendering_authorization_response["data"]["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "team": user["teams"][0],
                "rendering_id": rendering_id,
            },
            self.option["auth_secret"],
        )

        return Response(
            status=200,
            body=json.dumps({"token": token, "tokenData": body}),
            headers={"content_type": "application/json"},
        )

    # This method is never called, and not serve by an url route. Is it normal ?
    async def logout(self, request: Request) -> Response:
        return Response(status=204, body="", headers={})

    def _handle_error(self, method_name: LiteralMethod, request: Request, exc: Exception):
        if isinstance(exc, OpenIdException):
            return Response(
                status=exc.STATUS,
                body=json.dumps(
                    {
                        "error": exc.error,
                        "error_description": exc.error_description,
                        "state": exc.state,
                    }
                ),
            )
        elif isinstance(exc, AuthenticationException):
            return Response(
                status=exc.STATUS,
                body=json.dumps(
                    {
                        "error": exc.__class__.__name__,
                        "error_description": exc.args[0],
                    }
                ),
            )

        raise exc
