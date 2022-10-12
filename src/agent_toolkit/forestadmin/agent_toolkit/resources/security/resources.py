import json
import sys

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from urllib.parse import urljoin

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.resources.security.exceptions import AuthenticationException
from forestadmin.agent_toolkit.utils.authentication import ClientFactory, CustomClientOic
from forestadmin.agent_toolkit.utils.context import Request, Response
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.agent_toolkit.utils.token import build_jwt

LiteralMethod = Literal["authenticate", "callback"]


class Authentication(BaseResource):
    def __init__(self, options: Options):
        super(Authentication, self).__init__(options)
        self.callback_url = urljoin(options["agent_url"], "/forest/authentication/callback")

    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        return await method(request)

    async def authenticate(self, request: Request) -> Response:
        client: CustomClientOic = await ClientFactory.build(self.callback_url, self.option)
        if not request.body:
            raise AuthenticationException("renderingId is missing in the request's body")
        try:
            rendering_id = int(request.body["renderingId"])
        except KeyError:
            raise AuthenticationException("renderingId is missing in the request's body")
        except ValueError:
            raise AuthenticationException("renderingId should be an integer")

        authorization_url = client.get_authorization_url(json.dumps({"renderingId": rendering_id}))

        return Response(
            status=200,
            body=json.dumps({"authorizationUrl": authorization_url}),
            headers={"content_type": "application/json"},
        )

    async def callback(self, request: Request) -> Response:
        client: CustomClientOic = await ClientFactory.build(self.callback_url, self.option)
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

    async def logout(self, request: Request) -> Response:
        return Response(status=204, body="", headers={})
