import json
from typing import Any, Dict, Optional, TypedDict

from aiohttp import ClientSession, client_exceptions
from aiohttp.web import HTTPException
from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestSchema


class ForestHttpApiException(AgentToolkitException):
    pass


class HttpOptions(TypedDict):
    env_secret: str
    server_url: str


class ForestHttpApi:
    @staticmethod
    def build_endpoint(server_url: str, url: str):
        return f"{server_url}{url}"

    @classmethod
    async def get_environment_permissions(cls, options: HttpOptions):
        endpoint = cls.build_endpoint(options["server_url"], "/liana/v4/permissions/environment")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_users(cls, options: HttpOptions):
        endpoint = cls.build_endpoint(options["server_url"], "/liana/v4/permissions/users")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_rendering_permissions(cls, rendering_id: int, options: HttpOptions):
        endpoint = cls.build_endpoint(options["server_url"], f"/liana/v4/permissions/renderings/{rendering_id}")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_open_id_issuer_metadata(cls, options: HttpOptions) -> Dict[str, Any]:
        endpoint = cls.build_endpoint(options["server_url"], "/oidc/.well-known/openid-configuration")
        return await cls.get(endpoint, {"forest-secret-key": options["env_secret"]})

    @classmethod
    async def get_rendering_authorization(cls, rendering_id: int, access_token: str, options: HttpOptions):
        endpoint = cls.build_endpoint(options["server_url"], f"/liana/v2/renderings/{rendering_id}/authorization")
        return await cls.get(
            endpoint,
            {
                "forest-token": access_token,
                "forest-secret-key": options["env_secret"],
            },
        )

    @classmethod
    async def get_ip_white_list_rules(cls, options: HttpOptions):
        endpoint = cls.build_endpoint(options["server_url"], "/liana/v1/ip-whitelist-rules")
        return await cls.get(endpoint, {"forest-secret-key": options["env_secret"]})

    @staticmethod
    async def get(endpoint: str, headers: Dict[str, str]) -> Dict[str, Any]:
        async with ClientSession() as session:
            try:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    raise HTTPException(text=await response.text(), headers=headers)
            except Exception as exc:
                await ForestHttpApi._handle_server_error(endpoint, exc)

    @staticmethod
    async def post(endpoint: str, body: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        async with ClientSession() as session:
            try:
                async with session.post(endpoint, json=body, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    if response.status == 204:
                        return None
                    if str(response.status).startswith("4") or str(response.status).startswith("5"):
                        raise HTTPException(text=await response.text(), headers=headers)
            except Exception as exc:
                await ForestHttpApi._handle_server_error(endpoint, exc)

    @staticmethod
    async def _handle_server_error(endpoint: str, error: Exception) -> Exception:
        new_error = None
        if isinstance(error, client_exceptions.ClientConnectorCertificateError):
            new_error = ForestHttpApiException(
                "ForestAdmin server TLS certificate cannot be verified. "
                + "Please check that your system time is set properly."
            )

        elif isinstance(error, HTTPException):
            server_message = None
            if error.status in [-1, 0, 502]:
                new_error = ForestHttpApiException("Failed to reach ForestAdmin server. Are you online?")
            elif error.status == 404:
                new_error = ForestHttpApiException(
                    "ForestAdmin server failed to find the project related to the envSecret you configured."
                    + " Can you check that you copied it properly in the Forest initialization?"
                )
            elif error.status == 503:
                new_error = ForestHttpApiException(
                    "Forest is in maintenance for a few minutes. We are upgrading your experience in "
                    + "the forest. We just need a few more minutes to get it right."
                )
            elif error.body:
                try:
                    err_body = json.loads(error.body)
                    err_body = err_body.get("errors", [])
                    if len(err_body) > 0:
                        server_message = err_body[0].get("detail")
                except Exception:
                    server_message = None

            if new_error is None and server_message is not None:
                new_error = ForestHttpApiException(f"Failed to fetch {endpoint}: {server_message}.")

        if new_error is None:
            new_error = ForestHttpApiException(f"Failed to fetch {endpoint}: {error}")

        ForestLogger.log("error", ". ".join(new_error.args))
        raise new_error

    @classmethod
    async def send_schema(cls, options: HttpOptions, schema: ForestSchema) -> bool:
        ret = await cls.post(
            cls.build_endpoint(options["server_url"], "/forest/apimaps/hashcheck"),
            {"schemaFileHash": schema["meta"]["schemaFileHash"]},
            {"forest-secret-key": options["env_secret"], "content-type": "application/json"},
        )

        if ret["sendSchema"] is True:
            ForestLogger.log("info", "Schema was updated, sending new version.")
            await cls.post(
                cls.build_endpoint(options["server_url"], "/forest/apimaps"),
                schema,
                {"forest-secret-key": options["env_secret"], "content-type": "application/json"},
            )
        else:
            ForestLogger.log("info", "Schema was not updated since last run.")
