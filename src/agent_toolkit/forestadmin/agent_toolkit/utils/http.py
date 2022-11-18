import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Any, Dict, Optional

import aiohttp
from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.options import Options


class ForestHttpApiException(AgentToolkitException):
    pass


class HttpOptions(TypedDict):
    env_secret: str
    forest_server_url: str
    is_production: bool


class ForestHttpApi:
    @staticmethod
    def build_enpoint(forest_server_url: str, url: str):
        return f"{forest_server_url}{url}"

    @classmethod
    async def get_open_id_issuer_metadata(cls, option: Options) -> Dict[str, Any]:
        endpoint = cls.build_enpoint(option["forest_server_url"], "/oidc/.well-known/openid-configuration")
        response = await cls.get(endpoint, {"forest-secret-key": option["env_secret"]})
        return response

    @classmethod
    async def get_rendering_authorization(cls, rendering_id: int, access_token: str, option: Options):
        endpoint = cls.build_enpoint(option["forest_server_url"], f"/liana/v2/renderings/{rendering_id}/authorization")
        response = await cls.get(
            endpoint,
            {
                "forest-token": access_token,
                "forest-secret-key": option["env_secret"],
            },
        )
        return response

    @classmethod
    async def get_permissions(cls, option: HttpOptions, rendering_id: int) -> Dict[str, Any]:  # type: ignore
        endpoint = cls.build_enpoint(option["forest_server_url"], f"/liana/v3/permissions?renderingId={rendering_id}")
        headers = {"forest-secret-key": option["env_secret"]}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(endpoint, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
            except aiohttp.ClientError:
                raise ForestHttpApiException(f"Failed to fetch {endpoint}")

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
            except aiohttp.ClientError:
                raise ForestHttpApiException(f"Failed to fetch {endpoint}")

    @staticmethod
    async def post(endpoint: str, body: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(endpoint, json=body, headers=headers) as response:
                    print("api map upload status", response.status)
                    if response.status == 200:
                        return await response.json()
                    return None
            except aiohttp.ClientError:
                raise ForestHttpApiException(f"Failed to fetch {endpoint}")
