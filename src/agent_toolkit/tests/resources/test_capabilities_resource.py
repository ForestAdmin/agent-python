import asyncio
import importlib
import json
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import forestadmin.agent_toolkit.resources.capabilities
import forestadmin.agent_toolkit.resources.collections.crud
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, Response, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType


def authenticate_mock(fn):
    async def wrapped2(self, request):
        request.user = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

        return await fn(self, request)

    return wrapped2


def ip_white_list_mock(fn):
    async def wrapped(self, request: Request, *args, **kwargs):
        return await fn(self, request, *args, **kwargs)

    return wrapped


patch("forestadmin.agent_toolkit.resources.collections.decorators.authenticate", authenticate_mock).start()
patch("forestadmin.agent_toolkit.resources.collections.decorators.ip_white_list", ip_white_list_mock).start()
# how to mock decorators, and why they are not testable :
# https://dev.to/stack-labs/how-to-mock-a-decorator-in-python-55jc

importlib.reload(forestadmin.agent_toolkit.resources.capabilities)
from forestadmin.agent_toolkit.resources.capabilities import CapabilitiesResource  # noqa: E402


class TestCapabilitiesResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.permission_service = Mock(PermissionService)
        cls.ip_white_list_service = Mock(IpWhiteListService)
        cls.ip_white_list_service.is_enable = AsyncMock(return_value=False)
        cls.options = Options(
            auth_secret="fake_secret",
            env_secret="fake_secret",
            server_url="http://fake:5000",
            prefix="",
            is_production=False,
        )  # type:ignore

        cls.datasource = Datasource()
        Collection.__abstractmethods__ = set()  # type:ignore # to instantiate abstract class
        cls.book_collection = Collection("Book", cls.datasource)  # type:ignore
        cls.book_collection.add_fields(
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([Operator.EQUAL, Operator.IN, Operator.GREATER_THAN, Operator.LESS_THAN]),
                },
                "name": {
                    "column_type": PrimitiveType.STRING,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([]),
                },
                "cost": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": False,
                    "type": FieldType.COLUMN,
                    "filter_operators": set([]),
                },
            }  # type:ignore
        )
        cls.datasource.add_collection(cls.book_collection)
        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

    def setUp(self) -> None:
        self.capabilities_resource = CapabilitiesResource(self.datasource, self.ip_white_list_service, self.options)

    def test_dispatch_should_not_dispatch_to_capabilities_when_no_post_request(self):
        for method in [RequestMethod.DELETE, RequestMethod.OPTIONS, RequestMethod.PUT]:
            request = Request(
                method=method,
                query=None,
                body=None,
                headers={},
                user=self.mocked_caller,
            )
            response: Response = self.loop.run_until_complete(
                self.capabilities_resource.dispatch(request, "capabilities")
            )

            self.assertEqual(response.status, 405)

    def test_dispatch_should_dispatch_POST_to_capabilities(self):
        request = Request(
            method=RequestMethod.POST,
            query=None,
            body={"collectionNames": ["Book"]},
            headers={},
            user=self.mocked_caller,
        )
        response: Response = self.loop.run_until_complete(self.capabilities_resource.dispatch(request, "capabilities"))
        self.assertEqual(response.status, 200)
        response_content = json.loads(response.body)
        self.assertEqual(
            response_content["collections"],
            [
                {
                    "name": "Book",
                    "fields": [
                        {
                            "name": "id",
                            "type": "Number",
                            "operators": ["equal", "greater_than", "in", "less_than"],
                        },
                        {"name": "name", "type": "String", "operators": []},
                        {"name": "cost", "type": "Number", "operators": []},
                    ],
                }
            ],
        )
