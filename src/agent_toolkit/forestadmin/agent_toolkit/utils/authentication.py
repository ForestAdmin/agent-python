import json
from typing import Any, Dict, Optional
from urllib.parse import urljoin

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.security.exceptions import OpenIdException
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from oic.oauth2.message import Message
from oic.oic import Client as OicClient
from oic.oic.message import AuthorizationRequest, AuthorizationResponse, ProviderConfigurationResponse
from oic.utils.settings import PyoidcSettings


class CustomClientOic(OicClient):
    SCOPE = ["openid", "email", "profile"]

    def __init__(self, verify_ssl: bool = True):
        super().__init__(settings=PyoidcSettings(verify_ssl=verify_ssl))

    def register(self, url: str, registration_token: Optional[str] = None, **kwargs):  # type: ignore
        """
        needed to avoid bj64 encoding in authorization header
        """
        req = self.create_registration_request(**kwargs)
        if self.events:
            self.events.store("Protocol request", req)
        headers = {"content-type": "application/json"}
        if registration_token is not None:
            headers["Authorization"] = "Bearer " + registration_token

        rsp = self.http_request(url, "POST", data=req.to_json(), headers=headers)

        self.handle_registration_info(rsp)
        self.redirect_uris = self.registration_response["redirect_uris"]

    def get_authorization_url(self, state: str) -> str:
        args: Dict[str, Any] = {
            "client_id": self.client_id,  # type: ignore
            "response_type": "code",
            "scope": self.SCOPE,
            "state": state,
            "redirect_uri": self.registration_response["redirect_uris"][0],
        }
        auth_req: AuthorizationRequest = self.construct_AuthorizationRequest(request_args=args)  # type: ignore
        return auth_req.request(self.authorization_endpoint)  # type: ignore

    def get_parsed_response(self, info: Dict[str, Any]) -> Message:
        if "error" in info:
            raise OpenIdException(
                "error given in the query GET params", info["error"], info["error_description"], info["state"]
            )
        return self.parse_response(  # type: ignore
            AuthorizationResponse, info=json.dumps(info), state=info["state"], scope=self.SCOPE
        )

    def get_access_token(self, authorization_response: Message):
        access_token = self.do_access_token_request(  # type: ignore
            state=authorization_response["state"],
            request_args={"code": authorization_response["code"]},
            skew=5,
            authn_method="",
        )
        return access_token


class ClientFactory:
    oic_client: Optional[CustomClientOic] = None

    @classmethod
    async def build(cls, options: Options) -> CustomClientOic:
        if cls.oic_client:
            return cls.oic_client

        issuer_metadata: Dict[str, Any] = await ForestHttpApi.get_open_id_issuer_metadata(options)

        client = CustomClientOic(options["verify_ssl"])
        client.register(  # type: ignore
            issuer_metadata["registration_endpoint"],
            registration_token=options["env_secret"],
        )
        client.handle_provider_config(
            ProviderConfigurationResponse(  # type: ignore
                jwks_uri=urljoin(issuer_metadata["issuer"], "oidc/jwks"),
                token_endpoint=urljoin(issuer_metadata["issuer"], "oidc/token"),
                authorization_endpoint=urljoin(issuer_metadata["issuer"], "oidc/auth"),
            ),
            issuer_metadata["issuer"],
        )
        cls.oic_client = client
        return cls.oic_client
