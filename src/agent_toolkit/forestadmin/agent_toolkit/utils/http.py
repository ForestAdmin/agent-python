from typing import Any, Dict, Optional, TypedDict

import aiohttp
from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestSchema


class ForestHttpApiException(AgentToolkitException):
    pass


class HttpOptions(TypedDict):
    env_secret: str
    forest_server_url: str


class ForestHttpApi:
    @staticmethod
    def build_endpoint(forest_server_url: str, url: str):
        return f"{forest_server_url}{url}"

    @classmethod
    async def get_environment_permissions(cls, options: HttpOptions):
        endpoint = cls.build_endpoint(options["forest_server_url"], "/liana/v4/permissions/environment")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_users(cls, options: HttpOptions):
        endpoint = cls.build_endpoint(options["forest_server_url"], "/liana/v4/permissions/users")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_rendering_permissions(cls, rendering_id: int, options: HttpOptions):
        endpoint = cls.build_endpoint(options["forest_server_url"], f"/liana/v4/permissions/renderings/{rendering_id}")
        headers = {"forest-secret-key": options["env_secret"]}
        return await cls.get(endpoint, headers)

    @classmethod
    async def get_open_id_issuer_metadata(cls, options: HttpOptions) -> Dict[str, Any]:
        endpoint = cls.build_endpoint(options["forest_server_url"], "/oidc/.well-known/openid-configuration")
        return await cls.get(endpoint, {"forest-secret-key": options["env_secret"]})

    @classmethod
    async def get_rendering_authorization(cls, rendering_id: int, access_token: str, options: HttpOptions):
        endpoint = cls.build_endpoint(
            options["forest_server_url"], f"/liana/v2/renderings/{rendering_id}/authorization"
        )
        return await cls.get(
            endpoint,
            {
                "forest-token": access_token,
                "forest-secret-key": options["env_secret"],
            },
        )

    @staticmethod
    async def get(endpoint: str, headers: Dict[str, str]) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    raise ForestHttpApiException(
                        f"Failed to fetch {endpoint} ({response.status}, {headers} {await response.text()})"
                    )
            except aiohttp.ClientError as exc:
                raise ForestHttpApiException(f"Failed to fetch {endpoint} : {exc}")

    @staticmethod
    async def post(endpoint: str, body: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=body, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
            except aiohttp.ClientError as exc:
                raise ForestHttpApiException(f"Failed to fetch {endpoint} : {exc}")

    @classmethod
    async def send_schema(cls, options: HttpOptions, schema: ForestSchema) -> bool:
        ret = await cls.post(
            cls.build_endpoint(options["forest_server_url"], "/forest/apimaps/hashcheck"),
            {"schemaFileHash": schema["meta"]["schemaFileHash"]},
            {"forest-secret-key": options["env_secret"], "content-type": "application/json"},
        )

        if ret["sendSchema"] is True:
            ForestLogger.log("info", "Schema was updated, sending new version.")
            await cls.post(
                cls.build_endpoint(options["forest_server_url"], "/forest/apimaps"),
                schema,
                {"forest-secret-key": options["env_secret"], "content-type": "application/json"},
            )
        else:
            ForestLogger.log("info", "Schema was not updated since last run.")
